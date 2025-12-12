from __future__ import annotations

import json
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from inference_service.core.config import get_settings
from inference_service.core.storage import JobStorage
from inference_service.jobs.service import JobService
from inference_service.models.schemas import BomOutput, DetectionsOutput, JobManifest

router = APIRouter(prefix="", tags=["jobs"])


def _job_service() -> JobService:
    settings = get_settings()
    storage = JobStorage(settings.data_dir)
    return JobService(storage=storage, pipeline_config=settings.pipeline.model_dump(mode="json"))


@router.post("/jobs")
def create_job(
    manifest: Annotated[str, Form(...)],
    svc: Annotated[JobService, Depends(_job_service)],
    renders: Annotated[list[UploadFile] | None, File()] = None,
) -> dict[str, Any]:
    payload = _parse_manifest(manifest)
    model = JobManifest.model_validate(payload)
    result = svc.create_job(manifest=model, renders=renders or [])
    return {"jobId": result.job_id, "state": result.state.model_dump(mode="json")}


@router.post("/jobs/{job_id}/run")
def run_job(
    job_id: str,
    svc: Annotated[JobService, Depends(_job_service)],
) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())

    try:
        result = svc.run_job(job_id=job_id, trace_id=trace_id)
        return {
            "traceId": trace_id,
            "jobId": job_id,
            "idempotent": result.idempotent,
            "state": result.state.model_dump(mode="json"),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Run failed: {e}") from e


@router.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    svc: Annotated[JobService, Depends(_job_service)],
) -> dict[str, Any]:
    try:
        state = svc.get_state(job_id=job_id)
        paths = svc.storage.paths(job_id)
        renders_count = 0
        if paths.renders_dir.exists():
            renders_count = len([p for p in paths.renders_dir.iterdir() if p.is_file()])
        return {
            "jobId": job_id,
            "state": state.model_dump(mode="json"),
            "metadata": {
                "rendersCount": renders_count,
                "hasDetections": paths.detections_path.exists(),
                "hasBom": paths.bom_path.exists(),
            },
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/jobs/{job_id}/detections")
def get_detections(
    job_id: str,
    svc: Annotated[JobService, Depends(_job_service)],
) -> dict[str, Any]:
    paths = svc.storage.paths(job_id)
    if not paths.detections_path.exists():
        raise HTTPException(status_code=404, detail=f"Detections not found for job: {job_id}")
    payload = svc.storage.read_json(paths.detections_path)
    out = DetectionsOutput.model_validate(payload)
    return out.model_dump(mode="json")


@router.get("/jobs/{job_id}/bom")
def get_bom(
    job_id: str,
    svc: Annotated[JobService, Depends(_job_service)],
) -> dict[str, Any]:
    paths = svc.storage.paths(job_id)
    if not paths.bom_path.exists():
        raise HTTPException(status_code=404, detail=f"BOM not found for job: {job_id}")
    payload = svc.storage.read_json(paths.bom_path)
    out = BomOutput.model_validate(payload)
    return out.model_dump(mode="json")


def _parse_manifest(text: str) -> dict[str, Any]:
    if not text:
        raise HTTPException(status_code=422, detail="manifest is required")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"manifest must be valid JSON: {e}") from e

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="manifest must be a JSON object")

    return payload
