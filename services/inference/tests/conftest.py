from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from inference_service.main import app


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    os.environ["INFERENCE_DATA_DIR"] = str(tmp_path / "jobs")
    with TestClient(app) as c:
        yield c
