from __future__ import annotations

from pathlib import Path

from assetlens_core.config.cli import eval_cmd, run_cmd
from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config


def test_eval_metrics_smoke(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    cfg = cfg.model_copy(update={"output_dir": tmp_path / "out"})
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
    run_cmd(config=cfg_path)
    eval_cmd(config=cfg_path, labels=Path("poc_data/2d_cells/labels_2d.json"))

