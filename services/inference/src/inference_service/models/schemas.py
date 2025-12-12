from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class JobManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    assetId: str | None = None
    metadata: dict[str, Any] | None = None


class JobState(BaseModel):
    jobId: str
    status: JobStatus
    createdAt: datetime
    updatedAt: datetime
    errorMessage: str | None = None


class BBox(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(gt=0.0, le=1.0)
    h: float = Field(gt=0.0, le=1.0)


class Detection(BaseModel):
    id: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BBox
    source: str


class DetectionsOutput(BaseModel):
    schemaVersion: str
    detections: list[Detection]


class BomItem(BaseModel):
    label: str
    count: int = Field(ge=0)
    aggregateConfidence: float = Field(ge=0.0, le=1.0)


class BomOutput(BaseModel):
    schemaVersion: str
    items: list[BomItem]
