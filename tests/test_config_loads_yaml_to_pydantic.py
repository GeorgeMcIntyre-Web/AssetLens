from __future__ import annotations

from pathlib import Path

from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config


def test_config_loads_yaml_to_pydantic() -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    assert cfg.dataset_dir.as_posix().endswith("poc_data/2d_cells")
    assert cfg.seed == 123
    assert cfg.run_id is not None

