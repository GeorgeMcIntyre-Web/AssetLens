from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


SCHEMA_VERSION_3D = "0.1.0"


class PartInstance3D(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    part_name: str
    bbox_3d: tuple[tuple[float, float, float], tuple[float, float, float]]
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, object] = Field(default_factory=dict)


class ModelResult3D(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION_3D)
    run_id: str
    model_id: str
    model_path: str
    part_instances: list[PartInstance3D] = Field(default_factory=list)


class Run3DSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION_3D)
    run_id: str
    num_models: int = Field(ge=0)
    num_instances: int = Field(ge=0)
    counts_by_part: dict[str, int] = Field(default_factory=dict)


class Run3DOutputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: Run3DSummary
    models: list[ModelResult3D]
