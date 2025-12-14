from __future__ import annotations

from pathlib import Path

from assetlens_core.pipelines.assembly_graph_builder import build_assembly_graph


def _scene_path() -> Path:
    return Path(__file__).parent / "fixtures" / "phase_e" / "scene_graph_min.json"


def test_subassembly_signature_reuse() -> None:
    graph = build_assembly_graph(_scene_path())
    sig_left = graph.nodes_by_id["clamp_left"].signature
    sig_right = graph.nodes_by_id["clamp_right"].signature
    assert sig_left == sig_right

