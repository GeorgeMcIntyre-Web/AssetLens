from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from ..domain.results_2d import SCHEMA_VERSION_2D


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def load_color_mapping(mapping_path: Path) -> dict[str, str]:
    if mapping_path is None:
        raise ValueError("mapping_path must not be None.")
    if mapping_path.exists() is not True:
        raise FileNotFoundError(f"color mapping not found: {mapping_path}")

    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) is not True:
        raise ValueError("color_to_part.json must be an object.")

    out: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) is not True:
            raise ValueError("color mapping keys must be strings.")
        if isinstance(v, str) is not True:
            raise ValueError("color mapping values must be strings.")
        out[k.lower()] = v
    return out


def convert_asset_id_images_to_labels(asset_dir: Path) -> Path:
    if asset_dir is None:
        raise ValueError("asset_dir must not be None.")
    if asset_dir.exists() is not True:
        raise FileNotFoundError(f"asset_dir not found: {asset_dir}")

    id_dir = asset_dir / "images_id"
    if id_dir.exists() is not True:
        raise FileNotFoundError(f"images_id not found under asset_dir: {id_dir}")

    mapping_path = asset_dir / "color_to_part.json"
    mapping = load_color_mapping(mapping_path)

    id_paths = [p for p in id_dir.glob("view_*.png") if p.is_file()]
    id_paths.sort()
    if id_paths:
        pass
    if not id_paths:
        raise RuntimeError(f"No ID images found in {id_dir}")

    images_out: dict[str, list[dict]] = {}

    for id_path in id_paths:
        arr = np.array(Image.open(id_path).convert("RGB"), dtype=np.uint8)
        h, w, _c = arr.shape

        flat = arr.reshape(-1, 3)
        colors = np.unique(flat, axis=0)

        dets: list[dict] = []
        for color in colors:
            rgb = (int(color[0]), int(color[1]), int(color[2]))
            if rgb == (0, 0, 0):
                continue

            hex_color = _rgb_to_hex(rgb).lower()
            part = mapping.get(hex_color)
            if part is None:
                raise ValueError(f"Color {hex_color} not in mapping for {id_path}")

            mask = np.all(arr == color, axis=-1)
            if bool(mask.any()) is not True:
                continue

            ys, xs = np.where(mask)
            min_x = int(xs.min())
            max_x = int(xs.max())
            min_y = int(ys.min())
            max_y = int(ys.max())

            bbox_w = int(max_x - min_x + 1)
            bbox_h = int(max_y - min_y + 1)

            indices = (ys * w + xs).astype(int).tolist()

            dets.append(
                {
                    "label": part,
                    "bbox": [min_x, min_y, bbox_w, bbox_h],
                    "mask_indices": indices,
                    "mask_width": int(w),
                    "mask_height": int(h),
                    "area": int(mask.sum()),
                    "color": hex_color,
                }
            )

        dets.sort(key=lambda d: (d["label"], d["bbox"]))
        images_out[id_path.name] = dets

    labels_path = asset_dir / "labels_2d.json"
    payload = {"schema_version": SCHEMA_VERSION_2D, "images": images_out}
    labels_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return labels_path


def write_meta_json(
    glb_path: Path,
    asset_dir: Path,
    seed: int,
    views: int,
    res: int,
) -> Path:
    if glb_path is None:
        raise ValueError("glb_path must not be None.")
    if asset_dir is None:
        raise ValueError("asset_dir must not be None.")
    if glb_path.exists() is not True:
        raise FileNotFoundError(f"glb_path not found: {glb_path}")
    if seed is None:
        raise ValueError("seed must not be None.")
    if views < 1:
        raise ValueError("views must be one or greater.")
    if res < 8:
        raise ValueError("res must be 8 or greater.")

    data = glb_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()

    payload = {
        "seed": int(seed),
        "views": int(views),
        "resolution": int(res),
        "glb_sha256": digest,
    }

    meta_path = asset_dir / "meta.json"
    meta_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return meta_path
