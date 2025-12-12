from __future__ import annotations

from fastapi import FastAPI

from inference_service.api.routes.jobs import router as jobs_router

app = FastAPI(title="Inference Service", version="0.1.0")
app.include_router(jobs_router)
