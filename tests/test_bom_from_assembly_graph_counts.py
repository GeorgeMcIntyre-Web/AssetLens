from __future__ import annotations

from pathlib import Path

from assetlens_core.pipelines.assembly_graph_builder import build_assembly_graph
from assetlens_core.pipelines.bom_builder import bom_from_assembly_graph


def _fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "phase_e"


def test_bom_from_assembly_graph_counts() -> None:
    scene_path = _fixture_dir() / "scene_graph_min.json"
    meta_path = _fixture_dir() / "meta_min.json"
    graph = build_assembly_graph(scene_path)
    bom = bom_from_assembly_graph(
        graph=graph,
        asset_id="asset_min",
        scene_graph_path=scene_path,
        meta_path=meta_path,
    )

    by_part = {line.part_name: line.quantity for line in bom.lines}
    assert by_part.get("clamp") == 2
    assert by_part.get("bolt") == 2
    assert [line.part_name for line in bom.lines] == sorted(by_part.keys())

