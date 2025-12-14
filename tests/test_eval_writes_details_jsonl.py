from __future__ import annotations

from pathlib import Path

from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config
from assetlens_core.eval.evaluation_2d import evaluate_2d
from assetlens_core.pipelines.pipeline_2d_assets import run_2d_batch


def test_eval_writes_details_jsonl(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    cfg = cfg.model_copy(update={"output_dir": tmp_path / "out"})
    outputs = run_2d_batch(cfg)
    summary = evaluate_2d(
        labels_path=Path("poc_data/2d_cells/labels_2d.json"),
        detections=outputs.detections,
        output_dir=cfg.output_dir,
    )
    assert summary.num_images > 0
    assert (cfg.output_dir / "eval_2d_details.jsonl").exists() is True

