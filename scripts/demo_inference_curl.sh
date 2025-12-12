#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-"http://127.0.0.1:8000"}

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

render_path="$tmp_dir/render.png"
printf 'dummy' > "$render_path"

manifest='{"assetId":"asset-123","metadata":{"example":true}}'

create_resp=$(curl -sS \
  -X POST "$BASE_URL/jobs" \
  -F "manifest=$manifest" \
  -F "renders=@$render_path;type=image/png")

echo "CREATE: $create_resp"

job_id=$(python - <<'PY'
import json,sys
print(json.loads(sys.stdin.read())['jobId'])
PY
<<<"$create_resp")

echo "jobId=$job_id"

run_resp=$(curl -sS -X POST "$BASE_URL/jobs/$job_id/run")
echo "RUN: $run_resp"

echo "STATUS:"
curl -sS "$BASE_URL/jobs/$job_id" | python -m json.tool

echo "DETECTIONS:"
curl -sS "$BASE_URL/jobs/$job_id/detections" | python -m json.tool

echo "BOM:"
curl -sS "$BASE_URL/jobs/$job_id/bom" | python -m json.tool
