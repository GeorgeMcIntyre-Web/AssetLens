from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..config.assembly_rules import AssemblyRules, classify_part, default_assembly_rules, normalize_part_name
from ..domain.assembly_graph import AssemblyGraph, AssemblyNode


def build_assembly_graph(scene_graph_path: Path, rules: AssemblyRules | None = None) -> AssemblyGraph:
    if scene_graph_path is None:
        raise ValueError("scene_graph_path must not be None.")
    if scene_graph_path.exists() is not True:
        raise FileNotFoundError(f"scene_graph.json not found: {scene_graph_path}")

    if rules is None:
        rules = default_assembly_rules()

    raw = json.loads(scene_graph_path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) is not True:
        raise ValueError("scene_graph.json root must be an object.")

    roots_raw = raw.get("roots")
    nodes_raw = raw.get("nodes")
    if isinstance(roots_raw, list) is not True:
        raise ValueError("scene_graph.json must contain roots list.")
    if isinstance(nodes_raw, list) is not True:
        raise ValueError("scene_graph.json must contain nodes list.")

    node_defs: dict[str, dict] = {}
    for item in nodes_raw:
        if isinstance(item, dict) is not True:
            raise ValueError("scene_graph nodes must be objects.")
        name = item.get("name")
        if isinstance(name, str) is not True:
            raise ValueError("scene_graph node name must be a string.")
        if name in node_defs:
            raise ValueError(f"Duplicate node name in scene_graph: {name}")
        node_defs[name] = item

    norm_names: dict[str, str] = {}
    parent_by_id: dict[str, str | None] = {}
    children_by_id: dict[str, list[str]] = {}

    for node_id, item in node_defs.items():
        norm_names[node_id] = normalize_part_name(node_id)
        parent = item.get("parent")
        if parent is not None:
            if isinstance(parent, str) is not True:
                raise ValueError(f"parent must be string or null for node {node_id}")
        parent_by_id[node_id] = parent

        children = item.get("children", [])
        if isinstance(children, list) is not True:
            raise ValueError(f"children must be list for node {node_id}")
        for c in children:
            if isinstance(c, str) is not True:
                raise ValueError(f"child name must be string under {node_id}")
        children_by_id[node_id] = _sort_children(children, norm_names)

    roots: list[str] = []
    for r in roots_raw:
        if isinstance(r, str) is not True:
            raise ValueError("roots items must be strings.")
        roots.append(r)

    roots = _sort_children(roots, norm_names)
    if roots:
        pass
    if not roots:
        raise ValueError("scene_graph.json contains no roots.")

    root_id = roots[0]
    if len(roots) != 1:
        root_id = "__root__"
        norm_names[root_id] = "root"
        parent_by_id[root_id] = None
        children_by_id[root_id] = roots

    signatures: dict[str, str] = {}

    def compute_sig(node_id: str) -> str:
        if node_id in signatures:
            return signatures[node_id]

        children = children_by_id.get(node_id, [])
        child_sigs: list[str] = []
        for c in children:
            child_sigs.append(compute_sig(c))
        payload = {"name": norm_names.get(node_id, ""), "children": child_sigs}
        raw_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
        sig = digest[:16]
        signatures[node_id] = sig
        return sig

    compute_sig(root_id)
    for node_id in sorted(children_by_id.keys()):
        compute_sig(node_id)

    nodes_by_id: dict[str, AssemblyNode] = {}
    for node_id in sorted(children_by_id.keys(), key=lambda n: (norm_names.get(n, ""), n)):
        name = node_id
        norm = norm_names.get(node_id, "")
        node_type = classify_part(name, rules)
        if node_type == rules.fallback_category:
            if children_by_id.get(node_id):
                node_type = "assembly"
        parent = parent_by_id.get(node_id)
        children = children_by_id.get(node_id, [])
        nodes_by_id[node_id] = AssemblyNode(
            node_id=node_id,
            name=name,
            normalized_name=norm,
            type=node_type,
            parent_node_id=parent,
            children=list(children),
            signature=signatures.get(node_id, ""),
            mesh_refs=[name] if node_id != "__root__" else [],
            confidence=1.0,
        )

    return AssemblyGraph(root_id=root_id, nodes_by_id=nodes_by_id)


def write_assembly_graph(output_path: Path, graph: AssemblyGraph) -> None:
    if output_path is None:
        raise ValueError("output_path must not be None.")
    if graph is None:
        raise ValueError("graph must not be None.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = graph.model_dump()
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _sort_children(children: list[str], norm_names: dict[str, str]) -> list[str]:
    if children is None:
        raise ValueError("children must not be None.")
    if norm_names is None:
        raise ValueError("norm_names must not be None.")

    return sorted(children, key=lambda c: (norm_names.get(c, normalize_part_name(c)), c))

