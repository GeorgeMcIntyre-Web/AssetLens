from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TypeVar, Type

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TwoDFakeRunnerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(True)
    max_instances_per_prompt: int = Field(3, ge=0, le=20)
    mask_width: int = Field(64, ge=8, le=2048)
    mask_height: int = Field(64, ge=8, le=2048)


class TwoDThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_confidence: float = Field(0.40, ge=0.0, le=1.0)
    min_mask_area_ratio: float = Field(0.02, ge=0.0, le=1.0)


class AssetLens2DConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: int = Field(0, ge=0)
    run_id: str | None = Field(default=None)
    output_dir: Path = Field(default=Path("outputs"))
    dataset_dir: Path = Field(default=Path("poc_data/2d_cells"))
    image_glob: str = Field(default="images/*.png")
    labels_path: Path | None = Field(default=None)
    thresholds: TwoDThresholds = Field(default_factory=TwoDThresholds)
    fake_runner: TwoDFakeRunnerConfig = Field(default_factory=TwoDFakeRunnerConfig)
    include_classes: list[str] = Field(
        default_factory=lambda: [
            "robots",
            "grippers",
            "fixtures",
            "safety_fence_panels",
            "light_curtains",
            "other",
        ]
    )

    @model_validator(mode="after")
    def _validate_paths_and_run_id(self) -> "AssetLens2DConfig":
        if self.output_dir is None:
            raise ValueError("output_dir must not be None.")
        if self.dataset_dir is None:
            raise ValueError("dataset_dir must not be None.")
        if self.image_glob is None:
            raise ValueError("image_glob must not be None.")
        if self.image_glob.strip() == "":
            raise ValueError("image_glob must not be empty.")

        if self.labels_path is not None:
            if self.labels_path.exists() is not True:
                raise FileNotFoundError(f"labels_path not found: {self.labels_path}")

        if self.run_id is not None:
            return self

        payload = self.model_dump(mode="json")
        payload.pop("run_id", None)
        data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        self.run_id = digest[:12]
        return self


class ThreeDFakeRunnerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(True)
    max_instances_per_part: int = Field(2, ge=0, le=50)


class AssetLens3DConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: int = Field(0, ge=0)
    run_id: str | None = Field(default=None)
    output_dir: Path = Field(default=Path("outputs"))
    dataset_dir: Path = Field(default=Path("poc_data/3d_cells"))
    model_glob: str = Field(default="models/*.*")
    labels_path: Path | None = Field(default=None)
    fake_runner: ThreeDFakeRunnerConfig = Field(default_factory=ThreeDFakeRunnerConfig)
    include_parts: list[str] = Field(
        default_factory=lambda: [
            "base",
            "arm",
            "tool",
        ]
    )

    @model_validator(mode="after")
    def _validate_paths_and_run_id(self) -> "AssetLens3DConfig":
        if self.output_dir is None:
            raise ValueError("output_dir must not be None.")
        if self.dataset_dir is None:
            raise ValueError("dataset_dir must not be None.")
        if self.model_glob is None:
            raise ValueError("model_glob must not be None.")
        if self.model_glob.strip() == "":
            raise ValueError("model_glob must not be empty.")

        if self.labels_path is not None:
            if self.labels_path.exists() is not True:
                raise FileNotFoundError(f"labels_path not found: {self.labels_path}")

        if self.run_id is not None:
            return self

        payload = self.model_dump(mode="json")
        payload.pop("run_id", None)
        data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        self.run_id = digest[:12]
        return self


T = TypeVar("T", bound=BaseModel)


def load_yaml_config(path: Path, model: Type[T]) -> T:
    if path is None:
        raise ValueError("config path must not be None.")
    if path.exists() is not True:
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    if isinstance(data, dict) is not True:
        raise ValueError("Config YAML root must be a mapping/object.")

    return model.model_validate(data)


def load_2d_config(path: Path) -> AssetLens2DConfig:
    return load_yaml_config(path=path, model=AssetLens2DConfig)


def load_3d_config(path: Path) -> AssetLens3DConfig:
    return load_yaml_config(path=path, model=AssetLens3DConfig)
