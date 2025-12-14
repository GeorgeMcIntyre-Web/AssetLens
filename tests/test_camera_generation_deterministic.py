from __future__ import annotations

from assetlens_core.glb.cameras import generate_turntable_cameras


def test_camera_generation_deterministic() -> None:
    cams1 = generate_turntable_cameras(num_views=12, seed=123)
    cams2 = generate_turntable_cameras(num_views=12, seed=123)
    assert cams1 == cams2


def test_camera_generation_changes_with_seed() -> None:
    cams1 = generate_turntable_cameras(num_views=12, seed=123)
    cams2 = generate_turntable_cameras(num_views=12, seed=124)
    assert cams1 != cams2

