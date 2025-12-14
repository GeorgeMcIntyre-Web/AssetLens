from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BomEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_ids: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)


class BomLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_name: str
    quantity: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: BomEvidence = Field(default_factory=BomEvidence)


class BomGeneratedFrom(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_graph: str
    meta: str


class BomResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str
    lines: list[BomLine] = Field(default_factory=list)
    generated_from: BomGeneratedFrom

