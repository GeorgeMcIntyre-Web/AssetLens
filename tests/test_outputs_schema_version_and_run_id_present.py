from __future__ import annotations

from pathlib import Path

from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config
from assetlens_core.pipelines.pipeline_2d_assets import run_2d_batch
from assetlens_core.domain.results_2d import SCHEMA_VERSION_2D


def test_outputs_schema_version_and_run_id_present(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    cfg = cfg.model_copy(update={"output_dir": tmp_path / "out"})
    outputs = run_2d_batch(cfg)
    assert outputs.summary.schema_version == SCHEMA_VERSION_2D
    assert outputs.summary.run_id

