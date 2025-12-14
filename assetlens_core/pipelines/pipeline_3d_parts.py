from __future__ import annotations

import json
from pathlib import Path

from ..config.config import AssetLens3DConfig
from ..config.logging_utils import get_logger
from ..domain.results_3d import ModelResult3D, PartInstance3D, Run3DOutputs, Run3DSummary
from ..sam_wrappers.sam3d_runner import Fake3DPartRunner, PartResult
from .bom_builder import build_bom_from_3d, write_bom


log = get_logger("assetlens.pipeline_3d")


def _find_models(dataset_dir: Path, model_glob: str) -> list[Path]:
    if dataset_dir is None:
        raise ValueError("dataset_dir must not be None.")
    if model_glob is None:
        raise ValueError("model_glob must not be None.")
    if dataset_dir.exists() is not True:
        raise FileNotFoundError(f"dataset_dir not found: {dataset_dir}")

    paths = [p for p in dataset_dir.glob(model_glob) if p.is_file()]
    paths.sort()
    return paths


def _to_instances(parts: list[PartResult]) -> list[PartInstance3D]:
    if parts is None:
        raise ValueError("parts must not be None.")

    out: list[PartInstance3D] = []
    for p in parts:
        out.append(
            PartInstance3D(
                model_id=p.model_id,
                part_name=p.part_name,
                bbox_3d=p.bbox_3d,
                confidence=float(p.confidence),
                metadata={"source": "fake3d"},
            )
        )
    out.sort(key=lambda i: (i.part_name, i.bbox_3d))
    return out


def _make_summary(run_id: str, models: list[ModelResult3D], parts: list[str]) -> Run3DSummary:
    if run_id is None:
        raise ValueError("run_id must not be None.")
    if models is None:
        raise ValueError("models must not be None.")
    if parts is None:
        raise ValueError("parts must not be None.")

    counts: dict[str, int] = {}
    for p in sorted(set(parts)):
        counts[p] = 0

    num_instances = 0
    for m in models:
        for inst in m.part_instances:
            if inst.part_name not in counts:
                counts[inst.part_name] = 0
            counts[inst.part_name] += 1
            num_instances += 1

    return Run3DSummary(
        run_id=run_id,
        num_models=len(models),
        num_instances=num_instances,
        counts_by_part=counts,
    )


def _write_outputs(output_dir: Path, summary: Run3DSummary, models: list[ModelResult3D]) -> None:
    if output_dir is None:
        raise ValueError("output_dir must not be None.")
    if summary is None:
        raise ValueError("summary must not be None.")
    if models is None:
        raise ValueError("models must not be None.")

    jsonl_path = output_dir / "run_3d.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for model in models:
            for inst in model.part_instances:
                payload = {
                    "schema_version": model.schema_version,
                    "run_id": model.run_id,
                    "model_id": model.model_id,
                    "model_path": model.model_path,
                    **inst.model_dump(),
                }
                f.write(json.dumps(payload, sort_keys=True) + "\n")

    summary_path = output_dir / "run_3d_summary.json"
    summary_path.write_text(
        json.dumps(summary.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    log.info(f"Wrote run_3d.jsonl and summary to {output_dir}")


def run_3d_batch(config: AssetLens3DConfig) -> Run3DOutputs:
    if config is None:
        raise ValueError("config must not be None.")

    fake_cfg = config.fake_runner
    if fake_cfg.enabled is not True:
        raise RuntimeError("Only Fake3DPartRunner is supported in PoC.")

    model_paths = _find_models(config.dataset_dir, config.model_glob)
    if model_paths:
        pass
    if not model_paths:
        raise RuntimeError(
            f"No models found for dataset_dir={config.dataset_dir} glob={config.model_glob}"
        )

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = Fake3DPartRunner(max_instances_per_part=fake_cfg.max_instances_per_part)

    models: list[ModelResult3D] = []
    for model_path in model_paths:
        parts = runner.run(
            model_path=str(model_path),
            part_names=config.include_parts,
            seed=config.seed,
        )
        instances = _to_instances(parts)
        models.append(
            ModelResult3D(
                run_id=config.run_id,
                model_id=model_path.name,
                model_path=str(model_path),
                part_instances=instances,
            )
        )

    summary = _make_summary(run_id=config.run_id, models=models, parts=config.include_parts)
    _write_outputs(output_dir=output_dir, summary=summary, models=models)
    bom, _counts = build_bom_from_3d(models=models, assembly_id=f"3d:{config.run_id}")
    write_bom(output_path=output_dir / "bom_3d.json", assembly=bom)
    return Run3DOutputs(summary=summary, models=models)

