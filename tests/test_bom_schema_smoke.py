from __future__ import annotations

import json
from pathlib import Path

from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config
from assetlens_core.pipelines.pipeline_2d_assets import run_2d_batch


def test_bom_schema_smoke(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    cfg = cfg.model_copy(update={"output_dir": tmp_path / "out"})
    run_2d_batch(cfg)

    bom_path = cfg.output_dir / "bom_2d.json"
    data = json.loads(bom_path.read_text(encoding="utf-8"))
    assert "assembly_id" in data
    assert "items" in data
    assert "children" in data

