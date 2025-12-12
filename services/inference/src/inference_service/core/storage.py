from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JobPaths:
    job_dir: Path

    @property
    def input_dir(self) -> Path:
        return self.job_dir / "input"

    @property
    def output_dir(self) -> Path:
        return self.job_dir / "output"

    @property
    def logs_dir(self) -> Path:
        return self.job_dir / "logs"

    @property
    def state_path(self) -> Path:
        return self.job_dir / "state.json"

    @property
    def manifest_path(self) -> Path:
        return self.input_dir / "job.json"

    @property
    def renders_dir(self) -> Path:
        return self.input_dir / "renders"

    @property
    def detections_path(self) -> Path:
        return self.output_dir / "detections.json"

    @property
    def bom_path(self) -> Path:
        return self.output_dir / "bom.json"

    @property
    def run_log_path(self) -> Path:
        return self.logs_dir / "run.jsonl"


@dataclass(frozen=True)
class JobStorage:
    base_dir: Path

    def paths(self, job_id: str) -> JobPaths:
        return JobPaths(self.base_dir / job_id)

    def ensure_job_dir(self, job_id: str) -> JobPaths:
        paths = self.paths(job_id)
        paths.input_dir.mkdir(parents=True, exist_ok=True)
        paths.output_dir.mkdir(parents=True, exist_ok=True)
        paths.logs_dir.mkdir(parents=True, exist_ok=True)
        paths.renders_dir.mkdir(parents=True, exist_ok=True)
        return paths

    def job_exists(self, job_id: str) -> bool:
        return self.paths(job_id).job_dir.exists()

    def atomic_write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        with tmp_path.open("w", encoding="utf-8") as f:
            f.write(data)
            f.write("\n")
        os.replace(tmp_path, path)

    def read_json(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
