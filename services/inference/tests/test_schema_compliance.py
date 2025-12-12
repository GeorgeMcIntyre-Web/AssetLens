from __future__ import annotations

import json

from inference_service.models.schemas import BomOutput, DetectionsOutput


def test_outputs_validate_against_shared_schemas(client):
    resp = client.post(
        "/jobs",
        data={"manifest": json.dumps({"assetId": "a"})},
        files={"renders": ("render.png", b"dummy", "image/png")},
    )
    assert resp.status_code == 200, resp.text
    job_id = resp.json()["jobId"]

    resp = client.post(f"/jobs/{job_id}/run")
    assert resp.status_code == 200, resp.text

    det = client.get(f"/jobs/{job_id}/detections").json()
    bom = client.get(f"/jobs/{job_id}/bom").json()

    DetectionsOutput.model_validate(det)
    BomOutput.model_validate(bom)
