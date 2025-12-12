## Inference backend

This repo contains a minimal, deterministic FastAPI backend under `services/inference`.

### Install

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Run (dev)

```bash
uvicorn inference_service.main:app --reload
```

### Test

```bash
ruff check .
pytest
```
