from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreprocessResult:
    render_paths: list[Path]


def preprocess(*, renders_dir: Path) -> PreprocessResult:
    if not renders_dir.exists():
        return PreprocessResult(render_paths=[])

    paths = [p for p in renders_dir.iterdir() if p.is_file()]
    paths.sort(key=lambda p: p.name)
    return PreprocessResult(render_paths=paths)
