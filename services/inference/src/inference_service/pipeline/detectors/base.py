from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from inference_service.models.schemas import JobManifest


@dataclass(frozen=True)
class RawDetection:
    label: str
    confidence: float
    bbox_xywh: tuple[float, float, float, float]


class Detector(ABC):
    @abstractmethod
    def detect(self, *, manifest: JobManifest, pipeline_config: dict[str, Any]) -> list[RawDetection]:
        raise NotImplementedError
