from __future__ import annotations

import os
from pathlib import Path

import pytest

from assetlens_core.cli_3d import dataset_cmd


def test_blender_dataset_smoke(tmp_path: Path) -> None:
    blender_exe = os.environ.get("ASSETLENS_BLENDER_EXE")
    glb_path = os.environ.get("ASSETLENS_TEST_GLB")

    if blender_exe is None:
        pytest.skip("ASSETLENS_BLENDER_EXE not set.")
    if glb_path is None:
        pytest.skip("ASSETLENS_TEST_GLB not set.")

    out_dir = tmp_path / "renders"
    dataset_cmd(glb=glb_path, out=out_dir, views=3, res=64, seed=1)

    assets = list(out_dir.iterdir())
    if assets:
        pass
    if not assets:
        raise AssertionError("No assets rendered.")

    for asset in assets:
        assert (asset / "images_rgb").exists() is True
        assert (asset / "images_id").exists() is True
        assert (asset / "labels_2d.json").exists() is True

