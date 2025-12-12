from __future__ import annotations

import json


def test_run_is_idempotent_when_done(client):
    manifest = {"assetId": "same"}
    resp = client.post(
        "/jobs",
        data={"manifest": json.dumps(manifest)},
        files={"renders": ("render.png", b"dummy", "image/png")},
    )
    assert resp.status_code == 200, resp.text
    job_id = resp.json()["jobId"]

    first_status = client.get(f"/jobs/{job_id}").json()["state"]

    resp = client.post(f"/jobs/{job_id}/run")
    assert resp.status_code == 200
    assert resp.json()["idempotent"] is False

    det1 = client.get(f"/jobs/{job_id}/detections").json()
    bom1 = client.get(f"/jobs/{job_id}/bom").json()
    state1 = client.get(f"/jobs/{job_id}").json()["state"]

    resp = client.post(f"/jobs/{job_id}/run")
    assert resp.status_code == 200
    assert resp.json()["idempotent"] is True

    det2 = client.get(f"/jobs/{job_id}/detections").json()
    bom2 = client.get(f"/jobs/{job_id}/bom").json()
    state2 = client.get(f"/jobs/{job_id}").json()["state"]

    assert det1 == det2
    assert bom1 == bom2
    assert state1["updatedAt"] == state2["updatedAt"]
    assert first_status["status"] == "CREATED"
