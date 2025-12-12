from __future__ import annotations

import json


def _create_and_run(client, manifest: dict) -> tuple[dict, dict]:
    resp = client.post(
        "/jobs",
        data={"manifest": json.dumps(manifest)},
        files={"renders": ("render.png", b"dummy", "image/png")},
    )
    assert resp.status_code == 200, resp.text
    job_id = resp.json()["jobId"]

    resp = client.post(f"/jobs/{job_id}/run")
    assert resp.status_code == 200, resp.text

    det = client.get(f"/jobs/{job_id}/detections").json()
    bom = client.get(f"/jobs/{job_id}/bom").json()
    return det, bom


def test_same_inputs_produce_same_outputs(client):
    manifest = {"assetId": "asset-123", "metadata": {"x": 1, "y": [2, 3]}}

    det1, bom1 = _create_and_run(client, manifest)
    det2, bom2 = _create_and_run(client, manifest)

    assert det1["detections"] == det2["detections"]
    assert bom1["items"] == bom2["items"]
    assert det1["schemaVersion"] == det2["schemaVersion"]
    assert bom1["schemaVersion"] == bom2["schemaVersion"]
