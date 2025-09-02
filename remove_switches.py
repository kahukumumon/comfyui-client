from __future__ import annotations

import argparse
import copy
import json
from typing import Any, Dict, List, Tuple, Optional, Set


# 制御入力キー（データ入力ではない可能性が高い）
CONTROL_INPUT_KEYS = {"select", "sel_mode", "mode"}


def _is_connection(value: Any) -> bool:
    """ComfyUI風JSONの入力参照 ["<node_id>", <output_index>] 判定。"""
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], (str, int))
        and isinstance(value[1], int)
    )


def _list_connection_inputs(node_obj: Dict[str, Any]) -> List[Tuple[str, List[Any]]]:
    """データ接続とみなせる inputs を列挙（制御入力っぽいキーは除外）。"""
    inputs: Dict[str, Any] = node_obj.get("inputs", {}) or {}
    conns: List[Tuple[str, List[Any]]] = []
    for key, val in inputs.items():
        if key in CONTROL_INPUT_KEYS:
            continue
        if _is_connection(val):
            conns.append((key, val))
    # 規則性のある any_01, any_02 ... 等の名称順で安定化
    conns.sort(key=lambda kv: kv[0])
    return conns


def _choose_upstream_connection_generic(node_obj: Dict[str, Any]) -> Optional[List[Any]]:
    """規則ベースで任意の Switch ノードから上流1本を選択。"""
    conns = _list_connection_inputs(node_obj)
    if not conns:
        return None
    # 単一ならそれ、複数なら名称順の先頭
    chosen = conns[0][1]
    return [chosen[0], int(chosen[1])]


def _replace_all_references(
    graph: Dict[str, Any], target_node_id: str, replacement: List[Any]
) -> None:
    """全ノードのinputs内で target_node_id 参照を replacement に置換する。"""
    for node_id, node in graph.items():
        if not isinstance(node, dict):
            continue
        inputs: Dict[str, Any] = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue

        for key, val in list(inputs.items()):
            # パターン1: 直接参照 ["id", idx]
            if _is_connection(val) and str(val[0]) == str(target_node_id):
                inputs[key] = [replacement[0], int(replacement[1])]
                continue

            # パターン2: 配列の中に参照が含まれることは基本ないが、念のため軽く走査
            if isinstance(val, list):
                if len(val) == 0:
                    continue
                # ネストが更にあるケースは想定薄なので最小限の対応
                # 例: [ ["id", 0], ["id", 1] ] のような構造は通常現れない
                # 見つけても最初の一致だけ置換
                for i, inner in enumerate(val):
                    if _is_connection(inner) and str(inner[0]) == str(target_node_id):
                        val[i] = [replacement[0], int(replacement[1])]
                        break


def _replace_references_selective(
    graph: Dict[str, Any],
    target_node_id: str,
    chosen_output_index: int,
    replacement: List[Any],
    drop_other_refs: bool = False,
) -> None:
    """target_node_id の出力 chosen_output_index 参照のみ置換。
    drop_other_refs=True の場合、非選択出力の参照は削除する。
    """
    for node_id, node in graph.items():
        if not isinstance(node, dict):
            continue
        inputs: Dict[str, Any] = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        for key in list(inputs.keys()):
            val = inputs[key]
            if _is_connection(val) and str(val[0]) == str(target_node_id):
                if int(val[1]) == int(chosen_output_index):
                    inputs[key] = [replacement[0], int(replacement[1])]
                elif drop_other_refs:
                    del inputs[key]
                continue
            if isinstance(val, list) and len(val) > 0:
                new_list = []
                changed = False
                for inner in val:
                    if _is_connection(inner) and str(inner[0]) == str(target_node_id):
                        if int(inner[1]) == int(chosen_output_index):
                            new_list.append([replacement[0], int(replacement[1])])
                            changed = True
                        elif not drop_other_refs:
                            new_list.append(inner)
                    else:
                        new_list.append(inner)
                if changed:
                    inputs[key] = new_list


def _resolve_constant_value(
    graph: Dict[str, Any], node_id: str, output_index: int = 0, visited: Optional[Set[str]] = None
) -> Optional[Any]:
    """上流に遡って定数値を解決。簡易対応のみ。"""
    if visited is None:
        visited = set()
    if node_id in visited:
        return None
    visited.add(node_id)

    node = graph.get(str(node_id))
    if not isinstance(node, dict):
        return None
    class_type = node.get("class_type", "")
    inputs: Dict[str, Any] = node.get("inputs", {}) or {}

    # 典型的な定数ホルダ
    if class_type in {"SimpleMathInt+", "SimpleMathFloat+", "SimpleMathBoolean+"}:
        if isinstance(inputs.get("value"), (int, float, bool)):
            return inputs["value"]
    if class_type in {"StringConstant", "StringConstantMultiline", "PrimitiveStringMultiline"}:
        val = inputs.get("string", inputs.get("value"))
        return val
    if class_type == "mxSlider":
        xi = inputs.get("Xi")
        if isinstance(xi, (int, float)):
            return xi

    # Any Switch は単純に最初のデータ入力へ遡る
    if "Any Switch" in class_type:
        conns = _list_connection_inputs(node)
        if conns:
            upstream = conns[0][1]
            return _resolve_constant_value(graph, str(upstream[0]), int(upstream[1]), visited)

    return None


def remove_switch_nodes(graph: Dict[str, Any]) -> Dict[str, Any]:
    """Switch系ノードをバイパスして削除したJSONを返す（汎用検出 + 選択出力考慮）。"""
    new_graph: Dict[str, Any] = copy.deepcopy(graph)

    # 対象ノード一覧を抽出
    switch_ids: List[str] = []
    for node_id, node_obj in new_graph.items():
        if not isinstance(node_obj, dict):
            continue
        class_type = node_obj.get("class_type", "")
        if isinstance(class_type, str) and "Switch" in class_type:
            switch_ids.append(str(node_id))

    # 置換と削除
    for sid in switch_ids:
        node_obj = new_graph.get(sid)
        if not isinstance(node_obj, dict):
            continue

        class_type = node_obj.get("class_type", "")
        inputs: Dict[str, Any] = node_obj.get("inputs", {}) or {}

        # ImpactInversedSwitch: select 上流が定数なら、その値で 0/1 出力を決定して選択出力のみ置換
        if "ImpactInversedSwitch" in class_type:
            sel_conn = inputs.get("select")
            data_conns = _list_connection_inputs(node_obj)
            inp_conn = data_conns[0][1] if data_conns else None

            sel_val: Optional[Any] = None
            if _is_connection(sel_conn):
                sel_val = _resolve_constant_value(new_graph, str(sel_conn[0]), int(sel_conn[1]))

            if inp_conn is not None and isinstance(sel_val, (int, float)):
                idx = int(round(sel_val))
                # 1/2 指定を 0/1 に補正
                if idx in (1, 2):
                    idx -= 1
                if idx < 0:
                    idx = 0
                if idx > 1:
                    idx = 1
                _replace_references_selective(new_graph, sid, idx, [inp_conn[0], int(inp_conn[1])])
                continue

        # select を持つSwitch（ImpactSwitchなど）: 定数が取れたらそのインデックス、無ければ最初
        if "select" in inputs:
            data_conns = _list_connection_inputs(node_obj)
            if data_conns:
                sel_conn = inputs.get("select")
                sel_val: Optional[Any] = None
                if _is_connection(sel_conn):
                    sel_val = _resolve_constant_value(new_graph, str(sel_conn[0]), int(sel_conn[1]))
                if isinstance(sel_val, (int, float)):
                    idx = int(round(sel_val))
                    if idx >= 1 and idx - 1 < len(data_conns):
                        chosen = data_conns[idx - 1][1]
                    else:
                        idx0 = idx if 0 <= idx < len(data_conns) else 0
                        chosen = data_conns[idx0][1]
                else:
                    chosen = data_conns[0][1]
                _replace_all_references(new_graph, sid, [chosen[0], int(chosen[1])])
                continue

        # それ以外は汎用的に最初のデータ入力へバイパス
        replacement = _choose_upstream_connection_generic(node_obj)
        if replacement is None:
            continue
        _replace_all_references(new_graph, sid, replacement)

    # 参照置換が終わってから削除（未参照でも削除）
    for sid in switch_ids:
        if sid in new_graph:
            del new_graph[sid]

    return new_graph


def transform_json_text(json_text: str) -> str:
    """JSON文字列を受け取り、Switchノードを除去したJSON文字列を返す。"""
    obj = json.loads(json_text)
    if not isinstance(obj, dict):
        raise ValueError("root JSON はオブジェクト(dict)である必要があります")
    transformed = remove_switch_nodes(obj)
    return json.dumps(transformed, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove/bypass Switch nodes in ComfyUI-style JSON")
    parser.add_argument("-i", "--input", type=str, default="-", help="入力JSONファイルパス。'-' でstdin")
    parser.add_argument("-o", "--output", type=str, default="-", help="出力JSONファイルパス。'-' でstdout")
    args = parser.parse_args()

    # 入力読み込み
    if args.input == "-":
        in_text = input() if False else None  # type: ignore[unreachable]
        # 上記は型チェック回避のためのダミー。実際は下でstdin全体を読む。
        import sys

        in_text = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            in_text = f.read()

    out_text = transform_json_text(in_text)

    if args.output == "-":
        print(out_text)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_text)


if __name__ == "__main__":
    main()


