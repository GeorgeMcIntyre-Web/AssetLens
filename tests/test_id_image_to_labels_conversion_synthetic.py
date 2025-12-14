from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from assetlens_core.pipelines.pipeline_3d_dataset import convert_asset_id_images_to_labels


def test_id_image_to_labels_conversion_synthetic(tmp_path: Path) -> None:
    asset_dir = tmp_path / "asset"
    id_dir = asset_dir / "images_id"
    id_dir.mkdir(parents=True)

    img = np.zeros((4, 4, 3), dtype=np.uint8)
    img[0:2, 0:2] = (255, 0, 0)
    img[2:4, 2:4] = (0, 255, 0)

    Image.fromarray(img).save(id_dir / "view_000.png")

    mapping = {"#ff0000": "part_a", "#00ff00": "part_b"}
    (asset_dir / "color_to_part.json").write_text(
        json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8"
    )

    labels_path = convert_asset_id_images_to_labels(asset_dir=asset_dir)
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    dets = labels["images"]["view_000.png"]

    assert len(dets) == 2
    assert dets[0]["label"] == "part_a"
    assert dets[0]["bbox"] == [0, 0, 2, 2]
    assert dets[1]["label"] == "part_b"
    assert dets[1]["bbox"] == [2, 2, 2, 2]

