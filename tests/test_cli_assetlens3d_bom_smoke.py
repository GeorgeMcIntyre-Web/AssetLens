from __future__ import annotations

from pathlib import Path

from assetlens_core.cli_3d import bom_cmd


def _fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "phase_e"


def test_cli_assetlens3d_bom_smoke(tmp_path: Path) -> None:
    renders_root = tmp_path / "renders"
    asset_dir = renders_root / "asset_min"
    asset_dir.mkdir(parents=True)

    (asset_dir / "scene_graph.json").write_text(
        (_fixture_dir() / "scene_graph_min.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (asset_dir / "meta.json").write_text(
        (_fixture_dir() / "meta_min.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    bom_cmd(renders=renders_root, out=out_dir)
    bom_1 = (out_dir / "asset_min" / "bom_3d.json").read_text(encoding="utf-8")

    bom_cmd(renders=renders_root, out=out_dir)
    bom_2 = (out_dir / "asset_min" / "bom_3d.json").read_text(encoding="utf-8")

    assert bom_1 == bom_2
    assert (out_dir / "asset_min" / "assembly_graph.json").exists() is True

