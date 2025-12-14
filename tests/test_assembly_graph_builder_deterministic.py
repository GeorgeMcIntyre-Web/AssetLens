from __future__ import annotations

import json
from pathlib import Path

from assetlens_core.pipelines.assembly_graph_builder import build_assembly_graph


def _fixture_path(name: str) -> Path:
    base = Path(__file__).parent / "fixtures" / "phase_e"
    return base / name


def test_assembly_graph_builder_deterministic() -> None:
    scene_path = _fixture_path("scene_graph_min.json")
    g1 = build_assembly_graph(scene_path)
    g2 = build_assembly_graph(scene_path)
    s1 = json.dumps(g1.model_dump(), sort_keys=True)
    s2 = json.dumps(g2.model_dump(), sort_keys=True)
    assert s1 == s2

