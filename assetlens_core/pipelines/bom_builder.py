from __future__ import annotations

import json
from pathlib import Path

from ..domain.asset_types import BomAssembly, BomItem
from ..domain.results_2d import Detection2D
from ..domain.assembly_graph import AssemblyGraph
from ..domain.bom_types import BomEvidence, BomGeneratedFrom, BomLine, BomResult
from ..config.assembly_rules import AssemblyRules, classify_part, default_assembly_rules


def build_bom_from_2d(detections: list[Detection2D], assembly_id: str) -> tuple[BomAssembly, dict[str, int]]:
    if detections is None:
        raise ValueError("detections must not be None.")
    if assembly_id is None:
        raise ValueError("assembly_id must not be None.")

    counts: dict[str, int] = {}
    scores_by_label: dict[str, list[float]] = {}
    sources_by_label: dict[str, list[str]] = {}

    for det in detections:
        label = det.label
        if label not in counts:
            counts[label] = 0
            scores_by_label[label] = []
            sources_by_label[label] = []
        counts[label] += 1
        scores_by_label[label].append(float(det.score))
        sources_by_label[label].append(det.image_path)

    items: list[BomItem] = []
    for label in sorted(counts.keys()):
        scores = scores_by_label.get(label, [])
        avg_score = 0.0
        if scores:
            avg_score = float(sum(scores) / float(len(scores)))
        sources = sorted(set(sources_by_label.get(label, [])))
        items.append(
            BomItem(
                part_name=label,
                quantity=int(counts[label]),
                confidence=avg_score,
                sources=sources,
            )
        )

    assembly = BomAssembly(assembly_id=assembly_id, items=items, children=[])
    return assembly, counts


def build_bom_from_3d(models: list["ModelResult3D"], assembly_id: str) -> tuple[BomAssembly, dict[str, int]]:
    if models is None:
        raise ValueError("models must not be None.")
    if assembly_id is None:
        raise ValueError("assembly_id must not be None.")

    from ..domain.results_3d import ModelResult3D

    instances = []
    for m in models:
        if isinstance(m, ModelResult3D) is not True:
            raise ValueError("models must be ModelResult3D instances.")
        instances.extend(m.part_instances)

    counts: dict[str, int] = {}
    scores_by_part: dict[str, list[float]] = {}
    sources_by_part: dict[str, list[str]] = {}

    for inst in instances:
        part = inst.part_name
        if part not in counts:
            counts[part] = 0
            scores_by_part[part] = []
            sources_by_part[part] = []
        counts[part] += 1
        scores_by_part[part].append(float(inst.confidence))
        sources_by_part[part].append(inst.model_id)

    items: list[BomItem] = []
    for part in sorted(counts.keys()):
        scores = scores_by_part.get(part, [])
        avg_score = 0.0
        if scores:
            avg_score = float(sum(scores) / float(len(scores)))
        sources = sorted(set(sources_by_part.get(part, [])))
        items.append(
            BomItem(
                part_name=part,
                quantity=int(counts[part]),
                confidence=avg_score,
                sources=sources,
            )
        )

    assembly = BomAssembly(assembly_id=assembly_id, items=items, children=[])
    return assembly, counts


def write_bom(output_path: Path, assembly: BomAssembly) -> None:
    if output_path is None:
        raise ValueError("output_path must not be None.")
    if assembly is None:
        raise ValueError("assembly must not be None.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(assembly.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def bom_from_assembly_graph(
    graph: AssemblyGraph,
    rules: AssemblyRules | None = None,
    asset_id: str | None = None,
    scene_graph_path: Path | None = None,
    meta_path: Path | None = None,
) -> BomResult:
    if graph is None:
        raise ValueError("graph must not be None.")

    if rules is None:
        rules = default_assembly_rules()

    if asset_id is None:
        asset_id = graph.root_id

    counts: dict[str, int] = {}
    confidences: dict[str, list[float]] = {}
    evidence_nodes: dict[str, list[str]] = {}
    evidence_sources: dict[str, list[str]] = {}

    for node in graph.nodes_by_id.values():
        if node.node_id == graph.root_id:
            continue
        node_type = node.type
        if node_type is None:
            node_type = classify_part(node.name, rules)
        if node_type == "assembly":
            continue
        if node_type in rules.subassembly_categories:
            continue
        if node_type == rules.fallback_category:
            if node.children:
                continue

        if node_type not in counts:
            counts[node_type] = 0
            confidences[node_type] = []
            evidence_nodes[node_type] = []
            evidence_sources[node_type] = []

        counts[node_type] += 1
        confidences[node_type].append(float(node.confidence))
        evidence_nodes[node_type].append(node.node_id)
        for src in node.mesh_refs:
            evidence_sources[node_type].append(src)

    lines: list[BomLine] = []
    for part_name in sorted(counts.keys()):
        confs = confidences.get(part_name, [])
        avg_conf = 0.0
        if confs:
            avg_conf = float(sum(confs) / float(len(confs)))
        node_ids = sorted(set(evidence_nodes.get(part_name, [])))
        sources = sorted(set(evidence_sources.get(part_name, [])))
        lines.append(
            BomLine(
                part_name=part_name,
                quantity=int(counts[part_name]),
                confidence=avg_conf,
                evidence=BomEvidence(node_ids=node_ids, source_files=sources),
            )
        )

    from_scene = ""
    from_meta = ""
    if scene_graph_path is not None:
        from_scene = str(scene_graph_path)
    if meta_path is not None:
        from_meta = str(meta_path)

    generated_from = BomGeneratedFrom(scene_graph=from_scene, meta=from_meta)
    return BomResult(asset_id=asset_id, lines=lines, generated_from=generated_from)
