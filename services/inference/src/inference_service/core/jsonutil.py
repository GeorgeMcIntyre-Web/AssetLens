from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_sha256_hex(value: Any) -> str:
    payload = value
    if not isinstance(value, str):
        payload = canonical_json(value)
    digest = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
    return digest
