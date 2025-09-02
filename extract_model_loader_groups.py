import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 入力と出力のパス
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON_PATH = os.path.join(ROOT_DIR, "00-I2v_ImageToVideo.json")
OUTPUT_DIR = os.path.join(ROOT_DIR, "out")
OUTPUT_JSON_PATH = os.path.join(OUTPUT_DIR, "model_loader_groups.json")


def safe_float(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def rect_from_any(d: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
    """
    bouding / bounding / bounds のいずれかを矩形とみなして取り出す。
    期待する形: { x, y, w, h } または { left, top, width, height }
    """
    if not isinstance(d, dict):
        return None
    # 1) bounding が配列/タプルの場合
    if "bounding" in d and isinstance(d["bounding"], (list, tuple)):
        b = d["bounding"]
        if len(b) >= 4:
            v0 = safe_float(b[0])
            v1 = safe_float(b[1])
            v2 = safe_float(b[2])
            v3 = safe_float(b[3])
            if None not in (v0, v1, v2, v3):
                return (v0, v1, v2, v3)  # type: ignore[return-value]

    # 2) bounds/rect など辞書型から抽出
    for key in ("bounds", "rect", "bounding"):
        v = d.get(key)
        if isinstance(v, dict):
            # x, y, w, h または left, top, width, height を想定
            x = safe_float(v.get("x", v.get("left")))
            y = safe_float(v.get("y", v.get("top")))
            w = safe_float(v.get("w", v.get("width")))
            h = safe_float(v.get("h", v.get("height")))
            if None not in (x, y, w, h):
                return (x, y, w, h)  # type: ignore[return-value]

    # 3) 直接 x,y,w,h を持っているケース
    x = safe_float(d.get("x", d.get("left")))
    y = safe_float(d.get("y", d.get("top")))
    w = safe_float(d.get("w", d.get("width")))
    h = safe_float(d.get("h", d.get("height")))
    if None not in (x, y, w, h):
        return (x, y, w, h)  # type: ignore[return-value]

    return None

def point_in_rect(px: float, py: float, rect: Tuple[float, float, float, float]) -> bool:
    x, y, w, h = rect
    return (x <= px <= x + w) and (y <= py <= y + h)


def node_position(node: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    # ノードの位置候補キーに広めに対応
    pos = node.get("position") or node.get("pos") or node.get("xy") or {}
    if isinstance(pos, dict):
        px = pos.get("x", pos.get("left"))
        py = pos.get("y", pos.get("top"))
    elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
        px, py = pos[0], pos[1]
    else:
        px = node.get("x")
        py = node.get("y")

    pxf = safe_float(px)
    pyf = safe_float(py)
    if pxf is None or pyf is None:
        return None
    return (pxf, pyf)


def extract_model_loader_groups(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    definitions = data.get("definitions") or {}
    subgraphs = definitions.get("subgraphs") or []

    target: Optional[Dict[str, Any]] = None
    for sg in subgraphs:
        if isinstance(sg, dict) and sg.get("name") == "ModelLoader":
            target = sg
            break

    if target is None:
        return []

    # ターゲットサブグラフのID
    target_subgraph_id: Optional[str] = None
    if isinstance(target.get("id"), (str, int)):
        target_subgraph_id = str(target.get("id"))

    # ルート nodes から、type がサブグラフIDのノードを特定（最初の一件）
    root_nodes = data.get("nodes") or []
    subgraph_node_id_str: Optional[str] = None
    if target_subgraph_id is not None:
        for nd in root_nodes:
            if not isinstance(nd, dict):
                continue
            if nd.get("type") == target_subgraph_id:
                nid = nd.get("id")
                if isinstance(nid, (str, int)):
                    subgraph_node_id_str = str(nid)
                break

    groups = target.get("groups") or []
    nodes = target.get("nodes") or []

    # ノードID→ノード辞書、また位置
    id_to_node: Dict[str, Dict[str, Any]] = {}
    node_positions: Dict[str, Tuple[float, float]] = {}
    for nd in nodes:
        if not isinstance(nd, dict):
            continue
        node_id = nd.get("id") or nd.get("node_id") or nd.get("uuid")
        if node_id is None:
            continue
        id_to_node[str(node_id)] = nd
        pos = node_position(nd)
        if pos is not None:
            node_positions[str(node_id)] = pos

    results: List[Dict[str, Any]] = []

    for gp in groups:
        if not isinstance(gp, dict):
            continue
        title = gp.get("title") or gp.get("name") or gp.get("label") or ""
        rect = rect_from_any(gp)

        # グループが直接 node IDs を持っている可能性
        raw_nodes = gp.get("nodes")
        listed_nodes: List[Any] = list(raw_nodes) if isinstance(raw_nodes, list) else []
        listed_nodes_str: List[str] = [str(n) for n in listed_nodes]

        contained_ids: List[str] = []

        # 1) 明示的に列挙されている nodes を採用
        for nid in listed_nodes_str:
            if nid in id_to_node:
                contained_ids.append(nid)

        # 2) 矩形があれば、位置で内包判定
        if rect is not None:
            for nid, pos in node_positions.items():
                if nid in contained_ids:
                    continue
                px, py = pos
                if point_in_rect(px, py, rect):
                    contained_ids.append(nid)

        # 3) ノードの中心やサイズでさらに厳密に見たい場合はここで拡張可能
        first_two = title.split(", ")[:2] if title else []
        trigger_folder_name = [f.split(" ")[0].strip() for f in first_two]
        if len(trigger_folder_name) < 2 and title:
            trigger_folder_name = title.split(" ")[:2]
        results.append({
            "subgraph_id": subgraph_node_id_str,
            "trigger_folder_name": trigger_folder_name,
            # "group_bounds": {
            #     "x": rect[0],
            #     "y": rect[1],
            #     "w": rect[2],
            #     "h": rect[3],
            # } if rect is not None else None,
            "node_ids": contained_ids,
            # "nodes": [id_to_node[nid] for nid in contained_ids if nid in id_to_node],
        })

    return results


def main() -> None:
    data = json.loads(Path(INPUT_JSON_PATH).read_text(encoding="utf-8"))
    results = extract_model_loader_groups(data)
    Path(OUTPUT_JSON_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    trigger_folder_names = (", ".join(result["trigger_folder_name"]) for result in results)
    Path("trigger_folder_names.txt").write_text("\n".join(trigger_folder_names), encoding="utf-8")



if __name__ == "__main__":
    main()
