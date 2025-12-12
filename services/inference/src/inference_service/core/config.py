from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineConfig(BaseModel):
    detector: str = "mock"
    schema_version: str = "1.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INFERENCE_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    data_dir: Path = Path("data/jobs")
    pipeline: PipelineConfig = PipelineConfig()


def get_settings() -> Settings:
    return Settings()
