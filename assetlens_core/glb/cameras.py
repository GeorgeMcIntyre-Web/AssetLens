from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraPose:
    name: str
    position: tuple[float, float, float]
    look_at: tuple[float, float, float]
    fov_deg: float


def _rand01(seed: int, key: str) -> float:
    if seed is None:
        raise ValueError("seed must not be None.")
    if key is None:
        raise ValueError("key must not be None.")

    digest = hashlib.sha256(f"{seed}|{key}".encode("utf-8")).digest()
    val = int.from_bytes(digest[:8], byteorder="little", signed=False)
    return float(val / 2**64)


def generate_turntable_cameras(
    num_views: int,
    seed: int,
    radius: float = 2.0,
) -> list[CameraPose]:
    if num_views is None:
        raise ValueError("num_views must not be None.")
    if num_views < 1:
        raise ValueError("num_views must be one or greater.")
    if seed is None:
        raise ValueError("seed must not be None.")
    if radius <= 0.0:
        raise ValueError("radius must be positive.")

    rings = [0.0]
    if num_views >= 3:
        rings = [0.0, 20.0, -20.0]

    elev_jitter = (_rand01(seed, "elev_base") - 0.5) * 5.0
    step = 2.0 * math.pi / float(num_views)

    cams: list[CameraPose] = []
    for i in range(num_views):
        az = step * float(i)
        jitter = (_rand01(seed, f"az|{i}") - 0.5) * step * 0.1
        az = az + jitter

        elev_deg = rings[i % len(rings)] + elev_jitter
        elev_rad = math.radians(elev_deg)

        x = radius * math.cos(az) * math.cos(elev_rad)
        y = radius * math.sin(az) * math.cos(elev_rad)
        z = radius * math.sin(elev_rad)

        cams.append(
            CameraPose(
                name=f"view_{i:03d}",
                position=(float(x), float(y), float(z)),
                look_at=(0.0, 0.0, 0.0),
                fov_deg=50.0,
            )
        )

    return cams

