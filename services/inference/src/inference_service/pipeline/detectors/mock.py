from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from inference_service.core.jsonutil import stable_sha256_hex
from inference_service.models.schemas import JobManifest
from inference_service.pipeline.detectors.base import Detector, RawDetection


def _seed_from_manifest_and_config(*, manifest: dict[str, Any], pipeline_config: dict[str, Any]) -> int:
    seed_material = {
        "manifest": manifest,
        "pipeline": pipeline_config,
    }
    digest = stable_sha256_hex(seed_material)
    return int(digest[:16], 16)


@dataclass(frozen=True)
class MockDetector(Detector):
    source_name: str = "mock"

    def detect(self, *, manifest: JobManifest, pipeline_config: dict[str, Any]) -> list[RawDetection]:
        manifest_payload = manifest.model_dump(mode="json")
        seed = _seed_from_manifest_and_config(manifest=manifest_payload, pipeline_config=pipeline_config)
        rng = random.Random(seed)

        labels = ["bolt", "nut", "washer", "panel", "bracket"]
        count = 3 + (seed % 3)

        detections: list[RawDetection] = []
        for _ in range(count):
            label = labels[rng.randrange(0, len(labels))]
            confidence = 0.5 + (rng.random() * 0.5)

            x = rng.random() * 0.8
            y = rng.random() * 0.8
            w = 0.1 + (rng.random() * 0.2)
            h = 0.1 + (rng.random() * 0.2)

            if x + w > 1.0:
                x = 1.0 - w
            if y + h > 1.0:
                y = 1.0 - h

            detections.append(RawDetection(label=label, confidence=confidence, bbox_xywh=(x, y, w, h)))

        return detections
