from __future__ import annotations

from pathlib import Path

import pytest

from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config
from assetlens_core.pipelines.pipeline_2d_assets import run_2d_batch


def test_config_validation_no_images_found_fails_fast(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    empty_dataset = tmp_path / "empty"
    empty_dataset.mkdir()
    cfg = cfg.model_copy(update={"dataset_dir": empty_dataset, "output_dir": tmp_path / "out"})
    with pytest.raises(RuntimeError):
        run_2d_batch(cfg)

