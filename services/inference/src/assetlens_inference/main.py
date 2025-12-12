from fastapi import FastAPI

app = FastAPI(title="AssetLens Inference", version="0.0.0")


@app.get("/health")
def health() -> dict:
    return {"ok": True}
