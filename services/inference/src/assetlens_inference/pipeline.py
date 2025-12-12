from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RenderInput(BaseModel):
    file: str
    width: int
    height: int


class PipelineConfig(BaseModel):
    engine: str
    model: str
    scoreThresholdBps: int = Field(ge=0, le=10000)
    nmsThresholdBps: int = Field(ge=0, le=10000)
    maxDetectionsPerImage: int = Field(ge=1, le=1000)
    configHashAlgorithm: str
    seedAlgorithm: str


class Inputs(BaseModel):
    renders: list[RenderInput] = Field(min_length=1)


class JobManifest(BaseModel):
    schemaVersion: str
    traceId: str
    pipeline: PipelineConfig
    inputs: Inputs


def _canonical_json(obj: Any) -> str:
    # Deterministic canonicalization for hashing (stable key order, no whitespace).
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def derive_config_hash(job: JobManifest) -> str:
    payload = {
        "schemaVersion": job.schemaVersion,
        "pipeline": job.pipeline.model_dump(),
        "inputs": job.inputs.model_dump(),
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def derive_seed(trace_id: str, config_hash: str) -> int:
    digest = hashlib.sha256(f"{trace_id}:{config_hash}".encode()).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def _sha256_file(path: Path) -> tuple[str, bytes]:
    b = path.read_bytes()
    d = hashlib.sha256(b).digest()
    return d.hex(), d


def run_job(job: JobManifest, repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Deterministic "mock pipeline" that produces stable outputs from:
    - job manifest (traceId + pipeline config)
    - render bytes (sha256)

    This is intended for PoC determinism tests and frontend mock-mode data loading.
    """
    config_hash = derive_config_hash(job)
    seed = derive_seed(job.traceId, config_hash)

    renders_out: list[dict[str, Any]] = []
    label_space = ["bolt", "nut", "plate"]

    for idx, r in enumerate(job.inputs.renders, start=1):
        render_path = repo_root / r.file
        image_sha256, image_digest = _sha256_file(render_path)

        # Deterministic box + label derived from image digest + job seed.
        # Keep everything integer to avoid float-rounding drift.
        w, h = r.width, r.height
        x = image_digest[0] % max(1, (w - 20))
        y = image_digest[1] % max(1, (h - 20))
        bw = 10 + (image_digest[2] % 20)
        bh = 10 + (image_digest[3] % 20)
        if x + bw > w:
            x = max(0, w - bw)
        if y + bh > h:
            y = max(0, h - bh)

        label = label_space[(image_digest[4] + (seed & 0xFF)) % len(label_space)]

        threshold = job.pipeline.scoreThresholdBps
        # Score is always >= threshold and <= 10000.
        score_span = max(0, 10000 - threshold)
        score_bps = threshold + (image_digest[5] % (score_span + 1))

        det_id = f"det-{idx:04d}"
        renders_out.append(
            {
                "file": r.file,
                "imageSha256": image_sha256,
                "width": w,
                "height": h,
                "detections": [
                    {
                        "id": det_id,
                        "label": label,
                        "scoreBps": score_bps,
                        "box": {"x": x, "y": y, "w": bw, "h": bh},
                    }
                ],
            }
        )

    detections = {
        "schemaVersion": "detections/v1",
        "traceId": job.traceId,
        "configHash": config_hash,
        "seed": seed,
        "renders": renders_out,
    }

    counts: dict[str, int] = {}
    for ro in renders_out:
        for d in ro["detections"]:
            counts[d["label"]] = counts.get(d["label"], 0) + 1

    bom = {
        "schemaVersion": "bom/v1",
        "traceId": job.traceId,
        "configHash": config_hash,
        "items": [{"label": k, "count": counts[k]} for k in sorted(counts.keys())],
    }

    return detections, bom


def load_job_manifest(job_path: Path) -> JobManifest:
    return JobManifest.model_validate_json(job_path.read_text(encoding="utf-8"))
