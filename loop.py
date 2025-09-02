# pip install watchdog requests
from pathlib import Path
import json
import uuid
import time
import requests
import remove_switches
from typing import Dict, Any, List, Set

COMFY = "http://127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())

CONFIG = json.loads(Path("config.json").read_text(encoding="utf-8"))
WORKFLOW_JSON = CONFIG["workflow"]
INPUT_DIR = CONFIG["input_dir"]
# 置換ポイント：あなたのWFのノード/フィールド位置
LOAD_NODE_ID = "1100"  # LoadImage ノードID
SAVE_PREFIX_POS = 0  # filename_prefix がある位置（配列index）
wf = json.loads(Path(WORKFLOW_JSON).read_text(encoding="utf-8"))
for idx, node in wf.items():
    if (
        node["class_type"] == "LoadImagesFromFolderKJ"
        and node["_meta"]["title"] == "LoadImage"
    ):
        LOAD_NODE_ID = idx
        break
wf[LOAD_NODE_ID]["inputs"]["folder"] = INPUT_DIR
# サブフォルダも探索できるよう既定を true に（存在すれば上書き）
try:
    wf[LOAD_NODE_ID]["inputs"]["include_subfolders"] = True
except Exception:
    pass

# モデルローダーグループ（トリガー → ノードID群）を読み込み
GROUPS_PATH = Path("out/model_loader_groups.json")
GROUPS: List[Dict[str, Any]] = []
if GROUPS_PATH.exists():
    try:
        GROUPS = json.loads(GROUPS_PATH.read_text(encoding="utf-8"))
    except Exception:
        GROUPS = []


def _path_contains_any_keyword(path: Path, keywords: List[str]) -> bool:
    p = str(path).lower()
    for kw in keywords:
        try:
            if kw and str(kw).lower() in p:
                return True
        except Exception:
            continue
    return False


def collect_skip_node_ids_for_path(target_path: Path) -> Set[str]:
    """各グループについて、パスにトリガーが含まれなければそのグループの node_ids をスキップ対象に追加。"""
    skip: Set[str] = set()
    for grp in GROUPS:
        sub_id = grp.get("subgraph_id")
        triggers = grp.get("trigger_folder_name") or []
        node_ids = grp.get("node_ids") or []
        if not _path_contains_any_keyword(target_path, [str(t) for t in triggers]):
            for nid in node_ids:
                nid_str = str(nid)
                if sub_id:
                    skip.add(f"{str(sub_id)}:{nid_str}")
                else:
                    skip.add(nid_str)
    return skip


def _drop_all_references(graph: Dict[str, Any], target_node_id: str) -> None:
    """graph 内の inputs から target_node_id 参照を取り除く。"""
    for node_id, node in graph.items():
        if not isinstance(node, dict):
            continue
        inputs: Dict[str, Any] = node.get("inputs", {}) or {}
        for key in list(inputs.keys()):
            val = inputs[key]
            # 直接参照 ["id", idx]
            if (
                isinstance(val, list)
                and len(val) == 2
                and isinstance(val[0], (str, int))
                and str(val[0]) == str(target_node_id)
            ):
                del inputs[key]
                continue
            # 配列内参照を簡易に除去
            if isinstance(val, list) and len(val) > 0:
                new_list: List[Any] = []
                changed = False
                for inner in val:
                    if (
                        isinstance(inner, list)
                        and len(inner) == 2
                        and isinstance(inner[0], (str, int))
                        and str(inner[0]) == str(target_node_id)
                    ):
                        changed = True
                        continue
                    new_list.append(inner)
                if changed:
                    inputs[key] = new_list


def bypass_nodes(graph: Dict[str, Any], node_ids_to_skip: Set[str]) -> Dict[str, Any]:
    """指定ノードを上流へバイパス（可能なら）し、最終的に削除する。
    - データ入力の最初の接続があれば、それへ置換してから削除
    - なければ参照を除去してから削除
    """
    new_graph: Dict[str, Any] = json.loads(json.dumps(graph))
    # サブグラフ対応: キーが "<subgraph_id>:<node_id>" の形式を想定し、":<node_id>" 末尾一致で対象キーを解決
    def _resolve_target_keys(g: Dict[str, Any], raw_ids: Set[str]) -> List[str]:
        keys: List[str] = []
        # 1) subgraph_id:id 形式は厳密一致で採用
        colon_ids = [rid for rid in raw_ids if ":" in str(rid)]
        for rid in colon_ids:
            rid_str = str(rid)
            if rid_str in g and rid_str not in keys:
                keys.append(rid_str)

        # 2) 非コロンIDはサブグラフ末尾一致（":<id>"）を優先
        plain_ids = [rid for rid in raw_ids if ":" not in str(rid)]
        for key in g.keys():
            if ":" in key:
                for rid in plain_ids:
                    if key.endswith(f":{str(rid)}") and key not in keys:
                        keys.append(key)
                        break

        # 3) それでも見つからないものは通常キー完全一致
        for rid in plain_ids:
            rid_str = str(rid)
            if rid_str in g and rid_str not in keys:
                keys.append(rid_str)
        return keys

    target_keys: List[str] = _resolve_target_keys(new_graph, node_ids_to_skip)
    for nid in list(target_keys):
        if str(nid) not in new_graph:
            continue
        node_obj: Dict[str, Any] = new_graph.get(str(nid)) or {}
        # データ入力の列挙（remove_switches のユーティリティを流用）
        try:
            conns = remove_switches._list_connection_inputs(node_obj)  # type: ignore[attr-defined]
        except Exception:
            conns = []

        if conns:
            # 先頭の接続にバイパス
            upstream = conns[0][1]
            try:
                remove_switches._replace_all_references(new_graph, str(nid), [upstream[0], int(upstream[1])])  # type: ignore[attr-defined]
            except Exception:
                # 失敗時は参照を全削除
                _drop_all_references(new_graph, str(nid))
        else:
            # 接続が無ければ参照を全削除
            _drop_all_references(new_graph, str(nid))

        # ノード本体を削除
        if str(nid) in new_graph:
            try:
                del new_graph[str(nid)]
            except Exception:
                pass
    return new_graph


def build_workflow(idx: int, path_for_decision: Path):
    wf[LOAD_NODE_ID]["inputs"]["start_index"] = idx
    # パスに応じてスキップ対象ノードを決定し、グラフに反映
    skip_ids = collect_skip_node_ids_for_path(path_for_decision) if GROUPS else set()
    graph = wf
    if skip_ids:
        graph = bypass_nodes(graph, skip_ids)
    # 最後に Switch ノードの除去最適化
    return remove_switches.remove_switch_nodes(graph)


def submit(idx: int, path_for_decision: Path):
    payload = {"prompt": build_workflow(idx, path_for_decision), "client_id": CLIENT_ID}
    r = requests.post(f"{COMFY}/prompt", json=payload, timeout=60)
    r.raise_for_status()
    print(f"[queued] index={idx} file={path_for_decision} prompt_id={r.json()['prompt_id']}")


def get_queue_status():
    r = requests.get(f"{COMFY}/queue", timeout=30)
    r.raise_for_status()
    return r.json()


def main_loop():
    # 入力PNGを再帰列挙し、順番に空き時のみ投入
    input_paths = list(Path(INPUT_DIR).rglob("*.png"))
    i = 0
    while i < len(input_paths):
        try:
            q = get_queue_status()
        except requests.RequestException as e:
            print(f"[queue check error] {e}")
            time.sleep(10)
            continue

        pending = 0
        try:
            # ComfyUI /queue の想定レスポンスに準拠
            pending = len(q.get("queue_pending", []))
        except (TypeError, ValueError, KeyError):
            pending = 0

        if pending == 0:
            submit(i, input_paths[i])
            # 次の投入まで10秒待機（完了監視はしない）
            i += 1
        time.sleep(10)


if __name__ == "__main__":
    # watchdog を使用しない運用に切替
    main_loop()
