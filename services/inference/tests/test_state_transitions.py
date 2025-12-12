from __future__ import annotations

import json


def _create_job(client, manifest: dict) -> str:
    resp = client.post(
        "/jobs",
        data={"manifest": json.dumps(manifest)},
        files={"renders": ("render.png", b"dummy", "image/png")},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["jobId"]


def test_created_to_done(client):
    job_id = _create_job(client, {"assetId": "a1"})

    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["state"]["status"] == "CREATED"

    resp = client.post(f"/jobs/{job_id}/run")
    assert resp.status_code == 200, resp.text
    assert resp.json()["state"]["status"] == "DONE"

    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["state"]["status"] == "DONE"


def test_failed_transition_on_bad_detector(client, monkeypatch):
    monkeypatch.setenv("INFERENCE_PIPELINE__DETECTOR", "does-not-exist")
    job_id = _create_job(client, {"assetId": "a2"})

    resp = client.post(f"/jobs/{job_id}/run")
    assert resp.status_code == 500

    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["state"]["status"] == "FAILED"
    assert resp.json()["state"]["errorMessage"]
