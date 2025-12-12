from __future__ import annotations

import json
from pathlib import Path

from assetlens_inference.pipeline import load_job_manifest, run_job


def _repo_root() -> Path:
    # services/inference/tests -> services/inference -> services -> repo root
    return Path(__file__).resolve().parents[3]


def test_determinism_uses_sample_data_golden_outputs() -> None:
    root = _repo_root()
    sample_dir = root / "sample-data"

    job = load_job_manifest(sample_dir / "job.json")

    detections_1, bom_1 = run_job(job, sample_dir)
    detections_2, bom_2 = run_job(job, sample_dir)

    assert detections_1 == detections_2
    assert bom_1 == bom_2

    expected_detections = json.loads((sample_dir / "expected" / "detections.json").read_text())
    expected_bom = json.loads((sample_dir / "expected" / "bom.json").read_text())

    assert detections_1 == expected_detections
    assert bom_1 == expected_bom
