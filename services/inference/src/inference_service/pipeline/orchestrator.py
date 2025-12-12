from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from inference_service.core.jsonl_logger import JsonlLogger
from inference_service.models.schemas import BomOutput, DetectionsOutput, JobManifest
from inference_service.pipeline.aggregate import aggregate_bom
from inference_service.pipeline.detectors.base import Detector
from inference_service.pipeline.detectors.mock import MockDetector
from inference_service.pipeline.normalize import normalize
from inference_service.pipeline.preprocess import preprocess


@dataclass(frozen=True)
class PipelineResult:
    detections: DetectionsOutput
    bom: BomOutput


def _select_detector(*, name: str) -> Detector:
    if name == "mock":
        return MockDetector()
    raise ValueError(f"Unknown detector: {name}")


def run_pipeline(
    *,
    manifest: JobManifest,
    renders_dir: Path,
    pipeline_config: dict[str, Any],
    logger: JsonlLogger,
    trace_id: str,
    job_id: str,
) -> PipelineResult:
    t_pipeline = time.perf_counter()

    t_pre = time.perf_counter()
    preprocess(renders_dir=renders_dir)
    logger.log(
        trace_id=trace_id,
        job_id=job_id,
        stage="preprocess",
        event="done",
        duration_ms=_ms(t_pre),
    )

    t_detect = time.perf_counter()
    detector = _select_detector(name=str(pipeline_config.get("detector", "mock")))
    raw = detector.detect(manifest=manifest, pipeline_config=pipeline_config)
    logger.log(trace_id=trace_id, job_id=job_id, stage="detect", event="done", duration_ms=_ms(t_detect))

    t_norm = time.perf_counter()
    dets = normalize(raw=raw, source="mock")
    logger.log(trace_id=trace_id, job_id=job_id, stage="normalize", event="done", duration_ms=_ms(t_norm))

    t_agg = time.perf_counter()
    bom_items = aggregate_bom(detections=dets)
    logger.log(trace_id=trace_id, job_id=job_id, stage="aggregate", event="done", duration_ms=_ms(t_agg))

    schema_version = str(pipeline_config.get("schema_version", "1.0"))
    detections_out = DetectionsOutput(schemaVersion=schema_version, detections=dets)
    bom_out = BomOutput(schemaVersion=schema_version, items=bom_items)

    logger.log(trace_id=trace_id, job_id=job_id, stage="pipeline", event="done", duration_ms=_ms(t_pipeline))

    return PipelineResult(detections=detections_out, bom=bom_out)


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000.0)
