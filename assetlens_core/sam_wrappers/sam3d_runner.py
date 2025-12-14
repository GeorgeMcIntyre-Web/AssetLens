from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class PartResult:
    model_id: str
    model_path: str
    part_name: str
    bbox_3d: tuple[tuple[float, float, float], tuple[float, float, float]]
    confidence: float


class Sam3DRunner(Protocol):
    def run(
        self,
        model_path: str,
        part_names: list[str],
        seed: int,
    ) -> list[PartResult]:
        ...


def _stable_seed(key: str, seed: int) -> int:
    if key is None:
        raise ValueError("key must not be None.")
    if seed is None:
        raise ValueError("seed must not be None.")

    digest = hashlib.sha256(f"{seed}|{key}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False)


class Fake3DPartRunner:
    def __init__(self, max_instances_per_part: int) -> None:
        if max_instances_per_part is None:
            raise ValueError("max_instances_per_part must not be None.")
        if max_instances_per_part < 0:
            raise ValueError("max_instances_per_part must be zero or greater.")
        self.max_n = int(max_instances_per_part)

    def run(
        self,
        model_path: str,
        part_names: list[str],
        seed: int,
    ) -> list[PartResult]:
        if model_path is None:
            raise ValueError("model_path must not be None.")
        if part_names is None:
            raise ValueError("part_names must not be None.")
        if seed is None:
            raise ValueError("seed must not be None.")

        if part_names:
            pass
        if not part_names:
            return []

        model_id = Path(model_path).name
        out: list[PartResult] = []
        for part in sorted(part_names):
            local_seed = _stable_seed(f"{model_id}|{part}", int(seed))
            rng = np.random.default_rng(local_seed)
            n = int(rng.integers(0, self.max_n + 1))
            if n == 0:
                continue
            for _i in range(n):
                min_xyz = (rng.random(3) * 0.8).astype(float)
                size = (rng.random(3) * 0.2 + 0.05).astype(float)
                max_xyz = np.minimum(min_xyz + size, 1.0)
                bbox = (tuple(min_xyz.tolist()), tuple(max_xyz.tolist()))
                confidence = float(0.5 + float(rng.random()) * 0.49)
                out.append(
                    PartResult(
                        model_id=model_id,
                        model_path=model_path,
                        part_name=part,
                        bbox_3d=bbox,
                        confidence=confidence,
                    )
                )
        return out
