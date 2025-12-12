FROM python:3.11-slim

WORKDIR /app/services/inference

COPY services/inference/pyproject.toml ./
COPY services/inference/src ./src

RUN pip install --no-cache-dir -e ".[dev]"

ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "assetlens_inference.main:app", "--host", "0.0.0.0", "--port", "8000"]
