from __future__ import annotations

from collections import defaultdict

from inference_service.models.schemas import BomItem, Detection


def aggregate_bom(*, detections: list[Detection]) -> list[BomItem]:
    counts: dict[str, int] = defaultdict(int)
    conf_sum: dict[str, float] = defaultdict(float)

    for det in detections:
        counts[det.label] += 1
        conf_sum[det.label] += float(det.confidence)

    items: list[BomItem] = []
    for label in sorted(counts.keys()):
        count = counts[label]
        if count <= 0:
            continue
        avg = conf_sum[label] / float(count)
        items.append(BomItem(label=label, count=count, aggregateConfidence=float(avg)))

    return items
