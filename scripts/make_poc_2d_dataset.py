from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from assetlens_core.sam_wrappers.sam2d_runner import FakeSamRunner
from assetlens_core.domain.results_2d import SCHEMA_VERSION_2D


DEFAULT_CLASSES = [
    "robots",
    "grippers",
    "fixtures",
    "safety_fence_panels",
    "light_curtains",
    "other",
]


def make_dataset(out_dir: Path, n: int, seed: int, width: int, height: int) -> None:
    if out_dir is None:
        raise ValueError("out_dir must not be None.")
    if n < 1:
        raise ValueError("n must be one or greater.")
    if seed < 0:
        raise ValueError("seed must be zero or greater.")
    if width < 8:
        raise ValueError("width must be 8 or greater.")
    if height < 8:
        raise ValueError("height must be 8 or greater.")

    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(int(seed))
    runner = FakeSamRunner(max_instances_per_label=2)
    labels: dict[str, list[dict]] = {}

    for i in range(1, n + 1):
        name = f"cell_{i:03d}.png"
        path = images_dir / name

        pixels = (rng.random((height, width, 3)) * 255).astype(np.uint8)
        Image.fromarray(pixels).save(path)

        masks = runner.run(
            image_path=str(path),
            labels=DEFAULT_CLASSES,
            width=width,
            height=height,
            seed=seed,
        )

        dets: list[dict] = []
        for m in masks:
            dets.append(
                {
                    "label": m.label,
                    "score": m.score,
                    "bbox": list(m.bbox),
                    "mask_indices": m.mask_indices,
                    "mask_width": m.mask_width,
                    "mask_height": m.mask_height,
                }
            )
        labels[name] = dets

    labels_path = out_dir / "labels_2d.json"
    payload = {
        "schema_version": SCHEMA_VERSION_2D,
        "images": labels,
        "seed": seed,
        "width": width,
        "height": height,
    }
    labels_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n", type=int, default=2)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--height", type=int, default=64)
    args = parser.parse_args()

    make_dataset(out_dir=args.out, n=args.n, seed=args.seed, width=args.width, height=args.height)


if __name__ == "__main__":
    main()

