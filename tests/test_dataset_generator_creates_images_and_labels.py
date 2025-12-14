from __future__ import annotations

from pathlib import Path

from scripts.make_poc_2d_dataset import make_dataset


def test_dataset_generator_creates_images_and_labels(tmp_path: Path) -> None:
    make_dataset(out_dir=tmp_path, n=2, seed=7, width=32, height=32)
    assert (tmp_path / "images" / "cell_001.png").exists() is True
    assert (tmp_path / "images" / "cell_002.png").exists() is True
    assert (tmp_path / "labels_2d.json").exists() is True

