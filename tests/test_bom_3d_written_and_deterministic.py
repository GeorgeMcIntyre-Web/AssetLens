from __future__ import annotations

from pathlib import Path

from assetlens_core.config.config import AssetLens3DConfig, load_yaml_config
from assetlens_core.pipelines.pipeline_3d_parts import run_3d_batch


def test_bom_3d_written_and_deterministic(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_3d.yaml"), AssetLens3DConfig)
    cfg = cfg.model_copy(update={"output_dir": tmp_path / "out"})

    run_3d_batch(cfg)
    bom_1 = (cfg.output_dir / "bom_3d.json").read_text(encoding="utf-8")

    run_3d_batch(cfg)
    bom_2 = (cfg.output_dir / "bom_3d.json").read_text(encoding="utf-8")

    assert bom_1 == bom_2

