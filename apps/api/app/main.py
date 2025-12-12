from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field


def _data_dir() -> Path:
    env = os.getenv("DATA_DIR", "/data")
    return Path(env)


def _jobs_dir() -> Path:
    return _data_dir() / "jobs"


def _job_dir(job_id: str) -> Path:
    return _jobs_dir() / job_id


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class JobSummary(BaseModel):
    id: str
    status: Literal["created", "running", "completed", "failed"]
    createdAt: str


class Detection(BaseModel):
    id: str
    assetType: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[float] = Field(min_length=4, max_length=4)


class Render(BaseModel):
    id: str
    imagePath: str
    width: int
    height: int
    detections: list[Detection]


class JobDetail(BaseModel):
    id: str
    status: Literal["created", "running", "completed", "failed"]
    createdAt: str
    job: dict[str, Any]
    renders: list[Render]


class ReviewInstance(BaseModel):
    detectionId: str
    accepted: bool | None = None
    relabelAssetType: str | None = None


class ReviewPayload(BaseModel):
    jobId: str
    updatedAt: str
    instances: list[ReviewInstance]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs")
def list_jobs() -> list[JobSummary]:
    jobs_dir = _jobs_dir()
    jobs_dir.mkdir(parents=True, exist_ok=True)

    items: list[JobSummary] = []
    for p in jobs_dir.iterdir():
        if not p.is_dir():
            continue
        meta_path = p / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text("utf-8"))
            items.append(JobSummary.model_validate(meta))
        except Exception:
            continue

    items.sort(key=lambda j: j.createdAt, reverse=True)
    return items[:50]


@app.post("/jobs")
async def create_job(
    job: UploadFile = File(...),
    renders: list[UploadFile] = File(default=[]),
) -> JobSummary:
    if job.filename is None:
        raise HTTPException(status_code=400, detail="job file missing")

    job_id = uuid.uuid4().hex
    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    job_json_path = job_dir / "job.json"
    job_bytes = await job.read()
    job_json_path.write_bytes(job_bytes)

    renders_dir = job_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)

    for up in renders:
        if up.filename is None:
            continue
        out = renders_dir / up.filename
        out.write_bytes(await up.read())

    meta = JobSummary(id=job_id, status="created", createdAt=_now_iso())
    (job_dir / "meta.json").write_text(meta.model_dump_json(), "utf-8")

    # Optional: seed a basic detail payload
    detail = {
        "id": job_id,
        "status": meta.status,
        "createdAt": meta.createdAt,
        "job": json.loads(job_bytes.decode("utf-8")),
        "renders": [],
    }
    (job_dir / "detail.json").write_text(json.dumps(detail), "utf-8")

    return meta


@app.post("/jobs/{job_id}/run")
def run_job(job_id: str) -> JobSummary:
    job_dir = _job_dir(job_id)
    meta_path = job_dir / "meta.json"
    detail_path = job_dir / "detail.json"

    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="job not found")

    meta = JobSummary.model_validate_json(meta_path.read_text("utf-8"))
    meta.status = "completed"  # PoC: complete immediately
    meta_path.write_text(meta.model_dump_json(), "utf-8")

    # PoC: If there are renders uploaded, create fake detections
    detail_raw = json.loads(detail_path.read_text("utf-8")) if detail_path.exists() else {}
    job_doc = detail_raw.get("job")
    if job_doc is None:
        job_json_path = job_dir / "job.json"
        job_doc = json.loads(job_json_path.read_text("utf-8"))

    renders_dir = job_dir / "renders"
    renders_payload: list[dict[str, Any]] = []
    if renders_dir.exists():
        for idx, p in enumerate(sorted(renders_dir.iterdir())):
            if not p.is_file():
                continue
            render_id = f"r{idx+1}"
            # Keep bbox values in image pixel space; frontend will scale.
            detections = [
                {
                    "id": f"d{idx+1}-1",
                    "assetType": "widget",
                    "confidence": 0.92,
                    "bbox": [50, 50, 200, 160],
                },
                {
                    "id": f"d{idx+1}-2",
                    "assetType": "gizmo",
                    "confidence": 0.81,
                    "bbox": [260, 120, 140, 110],
                },
            ]
            renders_payload.append(
                {
                    "id": render_id,
                    "imagePath": f"/jobs/{job_id}/renders/{p.name}",
                    "width": 640,
                    "height": 480,
                    "detections": detections,
                }
            )

    detail = {
        "id": job_id,
        "status": meta.status,
        "createdAt": meta.createdAt,
        "job": job_doc,
        "renders": renders_payload,
    }
    detail_path.write_text(json.dumps(detail), "utf-8")

    return meta


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> JobDetail:
    job_dir = _job_dir(job_id)
    detail_path = job_dir / "detail.json"
    if not detail_path.exists():
        raise HTTPException(status_code=404, detail="job not found")

    return JobDetail.model_validate_json(detail_path.read_text("utf-8"))


@app.get("/jobs/{job_id}/review")
def get_review(job_id: str) -> JSONResponse:
    job_dir = _job_dir(job_id)
    path = job_dir / "review.json"
    if not path.exists():
        return JSONResponse(status_code=404, content={"detail": "review not found"})

    return JSONResponse(content=json.loads(path.read_text("utf-8")))


@app.put("/jobs/{job_id}/review")
def put_review(job_id: str, payload: ReviewPayload) -> ReviewPayload:
    if payload.jobId != job_id:
        raise HTTPException(status_code=400, detail="jobId mismatch")

    job_dir = _job_dir(job_id)
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="job not found")

    (job_dir / "review.json").write_text(payload.model_dump_json(), "utf-8")
    return payload


@app.get("/jobs/{job_id}/renders/{filename}")
def get_render(job_id: str, filename: str):
    # Minimal file server for compose usage
    job_dir = _job_dir(job_id)
    p = job_dir / "renders" / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="render not found")

    return FileResponse(path=str(p))
