from __future__ import annotations

from pathlib import Path

from assetlens_core.config.config import AssetLens2DConfig, load_yaml_config
from assetlens_core.pipelines.pipeline_2d_assets import run_2d_batch


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pipeline_2d_uses_fake_runner_and_is_deterministic(tmp_path: Path) -> None:
    cfg = load_yaml_config(Path("config_2d.yaml"), AssetLens2DConfig)
    cfg = cfg.model_copy(update={"output_dir": tmp_path / "out"})

    out1 = run_2d_batch(cfg)
    run_jsonl_1 = _read_text(cfg.output_dir / "run_2d.jsonl")
    summary_1 = _read_text(cfg.output_dir / "run_2d_summary.json")

    out2 = run_2d_batch(cfg)
    run_jsonl_2 = _read_text(cfg.output_dir / "run_2d.jsonl")
    summary_2 = _read_text(cfg.output_dir / "run_2d_summary.json")

    assert out1.summary.run_id == out2.summary.run_id
    assert run_jsonl_1 == run_jsonl_2
    assert summary_1 == summary_2

