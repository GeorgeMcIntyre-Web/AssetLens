from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


SCHEMA_VERSION_2D = "0.2.0"


class Detection2D(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION_2D)
    run_id: str
    image_path: str
    label: str
    score: float = Field(ge=0.0, le=1.0)
    bbox: tuple[int, int, int, int]
    mask_indices: list[int]
    mask_width: int = Field(ge=1)
    mask_height: int = Field(ge=1)


class Run2DSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION_2D)
    run_id: str
    num_images: int = Field(ge=0)
    num_detections: int = Field(ge=0)
    counts_by_label: dict[str, int] = Field(default_factory=dict)


class Run2DOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: Run2DSummary
    detections: list[Detection2D]
