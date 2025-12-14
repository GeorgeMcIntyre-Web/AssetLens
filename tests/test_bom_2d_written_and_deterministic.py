from __future__ import annotations

from pathlib import Path

from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config
from assetlens_core.pipelines.pipeline_2d_assets import run_2d_batch


def test_bom_2d_written_and_deterministic(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    cfg = cfg.model_copy(update={"output_dir": tmp_path / "out"})

    run_2d_batch(cfg)
    bom_1 = (cfg.output_dir / "bom_2d.json").read_text(encoding="utf-8")

    run_2d_batch(cfg)
    bom_2 = (cfg.output_dir / "bom_2d.json").read_text(encoding="utf-8")

    assert bom_1 == bom_2

