from __future__ import annotations

from inference_service.models.schemas import BBox, Detection
from inference_service.pipeline.detectors.base import RawDetection


def normalize(*, raw: list[RawDetection], source: str) -> list[Detection]:
    detections: list[Detection] = []

    idx = 0
    for item in raw:
        idx += 1
        x, y, w, h = item.bbox_xywh
        detections.append(
            Detection(
                id=f"det-{idx}",
                label=item.label,
                confidence=float(item.confidence),
                bbox=BBox(x=float(x), y=float(y), w=float(w), h=float(h)),
                source=source,
            )
        )

    return detections
