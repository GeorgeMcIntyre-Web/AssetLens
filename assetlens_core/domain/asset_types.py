from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class AssetClass(Enum):
    ROBOT = "robots"
    GRIPPER = "grippers"
    FIXTURE = "fixtures"
    SAFETY_FENCE_PANEL = "safety_fence_panels"
    LIGHT_CURTAIN = "light_curtains"
    OTHER = "other"

    @staticmethod
    def from_key(key: str) -> "AssetClass":
        if key is None:
            raise ValueError("key must not be None.")

        for item in AssetClass:
            if item.value == key:
                return item

        raise ValueError(f"Unknown asset class key: {key}")


class SemanticPartType(Enum):
    CLAMP = "clamp"
    FINGER = "finger"
    CYLINDER = "cylinder"
    FRAME = "frame"
    BRACKET = "bracket"
    SENSOR = "sensor"
    PIN = "pin"
    BOLT = "bolt"
    UNKNOWN = "unknown"


class BomItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_name: str
    quantity: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)


class BomAssembly(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assembly_id: str
    items: list[BomItem] = Field(default_factory=list)
    children: list["BomAssembly"] = Field(default_factory=list)
