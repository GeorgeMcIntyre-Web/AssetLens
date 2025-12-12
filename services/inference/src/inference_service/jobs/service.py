from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from inference_service.core.jsonl_logger import JsonlLogger
from inference_service.core.storage import JobStorage
from inference_service.models.schemas import (
    BomOutput,
    DetectionsOutput,
    JobManifest,
    JobState,
    JobStatus,
)
from inference_service.pipeline.orchestrator import run_pipeline


@dataclass(frozen=True)
class CreateJobResult:
    job_id: str
    state: JobState


@dataclass(frozen=True)
class RunJobResult:
    job_id: str
    state: JobState
    idempotent: bool


@dataclass(frozen=True)
class JobService:
    storage: JobStorage
    pipeline_config: dict[str, Any]

    def create_job(self, *, manifest: JobManifest, renders: list[UploadFile]) -> CreateJobResult:
        job_id = str(uuid.uuid4())
        paths = self.storage.ensure_job_dir(job_id)

        manifest_payload = manifest.model_dump(mode="json")
        self.storage.atomic_write_json(paths.manifest_path, manifest_payload)

        for file in renders:
            filename = _safe_filename(file.filename)
            if not filename:
                continue
            out_path = paths.renders_dir / filename
            _write_upload_file(file=file, out_path=out_path)

        now = _utcnow()
        state = JobState(jobId=job_id, status=JobStatus.CREATED, createdAt=now, updatedAt=now)
        self.storage.atomic_write_json(paths.state_path, state.model_dump(mode="json"))

        return CreateJobResult(job_id=job_id, state=state)

    def get_state(self, *, job_id: str) -> JobState:
        paths = self.storage.paths(job_id)
        if not paths.state_path.exists():
            raise FileNotFoundError(f"Job not found: {job_id}")
        payload = self.storage.read_json(paths.state_path)
        return JobState.model_validate(payload)

    def run_job(self, *, job_id: str, trace_id: str) -> RunJobResult:
        paths = self.storage.paths(job_id)
        if not paths.state_path.exists():
            raise FileNotFoundError(f"Job not found: {job_id}")

        state = self.get_state(job_id=job_id)
        if state.status == JobStatus.DONE:
            if paths.detections_path.exists() and paths.bom_path.exists():
                return RunJobResult(job_id=job_id, state=state, idempotent=True)

        if state.status == JobStatus.RUNNING:
            raise RuntimeError(f"Job is already running: {job_id}")

        state = _transition(state=state, to=JobStatus.RUNNING)
        self.storage.atomic_write_json(paths.state_path, state.model_dump(mode="json"))

        logger = JsonlLogger(paths.run_log_path)
        t0 = time.perf_counter()
        logger.log(trace_id=trace_id, job_id=job_id, stage="run", event="start", duration_ms=0)

        try:
            manifest_payload = self.storage.read_json(paths.manifest_path)
            manifest = JobManifest.model_validate(manifest_payload)

            result = run_pipeline(
                manifest=manifest,
                renders_dir=paths.renders_dir,
                pipeline_config=self.pipeline_config,
                logger=logger,
                trace_id=trace_id,
                job_id=job_id,
            )

            _write_outputs(storage=self.storage, paths=paths, detections=result.detections, bom=result.bom)
            state = _transition(state=state, to=JobStatus.DONE)
            self.storage.atomic_write_json(paths.state_path, state.model_dump(mode="json"))

            logger.log(
                trace_id=trace_id,
                job_id=job_id,
                stage="run",
                event="done",
                duration_ms=_ms(t0),
            )

            return RunJobResult(job_id=job_id, state=state, idempotent=False)
        except Exception as e:
            state = _transition(state=state, to=JobStatus.FAILED, error_message=str(e))
            self.storage.atomic_write_json(paths.state_path, state.model_dump(mode="json"))

            logger.log(
                trace_id=trace_id,
                job_id=job_id,
                stage="run",
                event="failed",
                duration_ms=_ms(t0),
                errorMessage=str(e),
            )
            raise


def _write_outputs(*, storage: JobStorage, paths: Any, detections: DetectionsOutput, bom: BomOutput) -> None:
    storage.atomic_write_json(paths.detections_path, detections.model_dump(mode="json"))
    storage.atomic_write_json(paths.bom_path, bom.model_dump(mode="json"))


def _safe_filename(name: str | None) -> str:
    if not name:
        return ""
    base = Path(name).name
    base = base.replace("..", "")
    return base


def _write_upload_file(*, file: UploadFile, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def _transition(*, state: JobState, to: JobStatus, error_message: str | None = None) -> JobState:
    now = _utcnow()
    payload = state.model_dump(mode="json")
    payload["status"] = to.value
    payload["updatedAt"] = now
    payload["errorMessage"] = error_message
    if to != JobStatus.FAILED:
        payload["errorMessage"] = None
    return JobState.model_validate(payload)


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000.0)
