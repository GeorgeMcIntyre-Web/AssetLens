from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JsonlLogger:
    path: Path

    def log(
        self,
        *,
        trace_id: str,
        job_id: str,
        stage: str,
        event: str,
        duration_ms: int,
        **extra: Any,
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record: dict[str, Any] = {
            "ts": time.time(),
            "traceId": trace_id,
            "jobId": job_id,
            "stage": stage,
            "event": event,
            "durationMs": duration_ms,
        }
        if extra:
            record.update(extra)
        line = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.write("\n")
