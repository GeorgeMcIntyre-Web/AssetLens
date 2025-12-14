from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import hashlib
import numpy as np


@dataclass(frozen=True)
class MaskResult:
    image_path: str
    label: str
    score: float
    bbox: tuple[int, int, int, int]
    mask_indices: list[int]
    mask_width: int
    mask_height: int


class Sam2DRunner(Protocol):
    def run(
        self,
        image_path: str,
        labels: list[str],
        width: int,
        height: int,
        seed: int,
    ) -> list[MaskResult]:
        ...


def _stable_seed(key: str, seed: int) -> int:
    if key is None:
        raise ValueError("key must not be None.")
    if seed is None:
        raise ValueError("seed must not be None.")

    digest = hashlib.sha256(f"{seed}|{key}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False)


class FakeSamRunner:
    def __init__(self, max_instances_per_label: int) -> None:
        if max_instances_per_label is None:
            raise ValueError("max_instances_per_label must not be None.")
        if max_instances_per_label < 0:
            raise ValueError("max_instances_per_label must be zero or greater.")
        self.max_n = int(max_instances_per_label)

    def run(
        self,
        image_path: str,
        labels: list[str],
        width: int,
        height: int,
        seed: int,
    ) -> list[MaskResult]:
        if image_path is None:
            raise ValueError("image_path must not be None.")
        if labels is None:
            raise ValueError("labels must not be None.")
        if width < 1:
            raise ValueError("width must be one or greater.")
        if height < 1:
            raise ValueError("height must be one or greater.")

        if labels:
            pass
        if not labels:
            return []

        out: list[MaskResult] = []
        for label in sorted(labels):
            out.extend(self._predict_label(image_path=image_path, label=label, width=width, height=height, seed=seed))
        return out

    def _predict_label(
        self,
        image_path: str,
        label: str,
        width: int,
        height: int,
        seed: int,
    ) -> list[MaskResult]:
        local_seed = _stable_seed(f"{image_path}|{label}", seed)
        rng = np.random.default_rng(local_seed)
        n = int(rng.integers(0, self.max_n + 1))

        if n == 0:
            return []

        results: list[MaskResult] = []
        for idx in range(n):
            results.append(
                self._make_one(
                    image_path=image_path,
                    label=label,
                    width=width,
                    height=height,
                    rng=rng,
                    index=idx,
                )
            )
        return results

    def _make_one(
        self,
        image_path: str,
        label: str,
        width: int,
        height: int,
        rng: "np.random.Generator",
        index: int,
    ) -> MaskResult:
        score = float(0.30 + float(rng.random()) * 0.69)

        area_ratio = float(0.02 + float(rng.random()) * 0.15)
        target_area = int(width * height * area_ratio)
        target_area = max(target_area, 1)

        rect_w = int(np.sqrt(target_area))
        rect_w = max(rect_w, 1)
        rect_h = max(target_area // rect_w, 1)

        rect_w = min(rect_w, width)
        rect_h = min(rect_h, height)

        max_x = max(width - rect_w, 0)
        max_y = max(height - rect_h, 0)

        x = int(rng.integers(0, max_x + 1))
        y = int(rng.integers(0, max_y + 1))

        xs = np.arange(x, x + rect_w, dtype=int)
        ys = np.arange(y, y + rect_h, dtype=int)
        flat = (ys[:, None] * width + xs[None, :]).ravel()

        return MaskResult(
            image_path=image_path,
            label=label,
            score=score,
            bbox=(x, y, rect_w, rect_h),
            mask_indices=flat.tolist(),
            mask_width=width,
            mask_height=height,
        )
