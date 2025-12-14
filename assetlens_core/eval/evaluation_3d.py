from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..domain.results_3d import ModelResult3D, SCHEMA_VERSION_3D


class PerPartMetrics3D(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_name: str
    tp: int = Field(0, ge=0)
    fp: int = Field(0, ge=0)
    fn: int = Field(0, ge=0)
    precision: float = Field(0.0, ge=0.0, le=1.0)
    recall: float = Field(0.0, ge=0.0, le=1.0)
    f1: float = Field(0.0, ge=0.0, le=1.0)


class Eval3DSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION_3D)
    run_id: str
    num_models: int = Field(0, ge=0)
    count_accuracy: float = Field(0.0, ge=0.0, le=1.0)
    precision: float = Field(0.0, ge=0.0, le=1.0)
    recall: float = Field(0.0, ge=0.0, le=1.0)
    f1: float = Field(0.0, ge=0.0, le=1.0)
    per_part: list[PerPartMetrics3D] = Field(default_factory=list)


def _load_labels(path: Path) -> dict[str, list[dict]]:
    if path is None:
        raise ValueError("labels path must not be None.")
    if path.exists() is not True:
        raise FileNotFoundError(f"labels file not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) is not True:
        raise ValueError("labels JSON root must be an object.")

    models = raw.get("models")
    if models is None:
        models = raw
    if isinstance(models, dict) is not True:
        raise ValueError("labels models field must be an object.")

    out: dict[str, list[dict]] = {}
    for model_id, items in models.items():
        if isinstance(items, list) is not True:
            raise ValueError(f"labels for {model_id} must be a list.")
        out[model_id] = items
    return out


def _count_gt(items: list[dict]) -> dict[str, int]:
    if items is None:
        raise ValueError("items must not be None.")

    counts: dict[str, int] = {}
    for obj in items:
        if isinstance(obj, dict) is not True:
            raise ValueError("ground truth item must be an object.")
        part = obj.get("part_name")
        if part is None:
            raise ValueError("ground truth part_name missing.")
        if part not in counts:
            counts[part] = 0
        counts[part] += 1
    return counts


def _count_pred(instances: list["object"]) -> dict[str, int]:
    if instances is None:
        raise ValueError("instances must not be None.")

    counts: dict[str, int] = {}
    for inst in instances:
        part = getattr(inst, "part_name", None)
        if part is None:
            raise ValueError("predicted part_name missing.")
        if part not in counts:
            counts[part] = 0
        counts[part] += 1
    return counts


def _safe_div(num: float, den: float) -> float:
    if den == 0.0:
        return 0.0
    return float(num / den)


def evaluate_3d(labels_path: Path, models: list[ModelResult3D], output_dir: Path) -> Eval3DSummary:
    if labels_path is None:
        raise ValueError("labels_path must not be None.")
    if models is None:
        raise ValueError("models must not be None.")
    if output_dir is None:
        raise ValueError("output_dir must not be None.")

    if models:
        pass
    if not models:
        raise ValueError("models must not be empty.")

    labels_by_model = _load_labels(labels_path)
    model_ids = sorted(labels_by_model.keys())

    if model_ids:
        pass
    if not model_ids:
        raise ValueError("labels file contains no models.")

    pred_by_model = {m.model_id: m for m in models}

    run_id = models[0].run_id
    exact_models = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0
    per_part_acc: dict[str, dict[str, int]] = {}

    for model_id in model_ids:
        if model_id not in pred_by_model:
            raise ValueError(f"Missing prediction for labelled model: {model_id}")

        gt_counts = _count_gt(labels_by_model[model_id])
        pred_counts = _count_pred(pred_by_model[model_id].part_instances)

        union_parts = sorted(set(gt_counts.keys()) | set(pred_counts.keys()))

        mismatched = False
        for part in union_parts:
            gt_v = int(gt_counts.get(part, 0))
            pred_v = int(pred_counts.get(part, 0))

            tp = min(gt_v, pred_v)
            fp = max(pred_v - gt_v, 0)
            fn = max(gt_v - pred_v, 0)

            if part not in per_part_acc:
                per_part_acc[part] = {"tp": 0, "fp": 0, "fn": 0}

            per_part_acc[part]["tp"] += tp
            per_part_acc[part]["fp"] += fp
            per_part_acc[part]["fn"] += fn

            total_tp += tp
            total_fp += fp
            total_fn += fn

            if fp > 0:
                mismatched = True
            if fn > 0:
                mismatched = True

        if mismatched is not True:
            exact_models += 1

    precision = _safe_div(float(total_tp), float(total_tp + total_fp))
    recall = _safe_div(float(total_tp), float(total_tp + total_fn))
    f1 = _safe_div(2.0 * precision * recall, precision + recall)
    count_accuracy = _safe_div(float(exact_models), float(len(model_ids)))

    per_part: list[PerPartMetrics3D] = []
    for part in sorted(per_part_acc.keys()):
        acc = per_part_acc[part]
        tp = int(acc["tp"])
        fp = int(acc["fp"])
        fn = int(acc["fn"])
        p = _safe_div(float(tp), float(tp + fp))
        r = _safe_div(float(tp), float(tp + fn))
        f = _safe_div(2.0 * p * r, p + r)
        per_part.append(
            PerPartMetrics3D(
                part_name=part,
                tp=tp,
                fp=fp,
                fn=fn,
                precision=p,
                recall=r,
                f1=f,
            )
        )

    summary = Eval3DSummary(
        run_id=run_id,
        num_models=len(model_ids),
        count_accuracy=count_accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        per_part=per_part,
    )

    _write_eval_outputs(output_dir=output_dir, summary=summary)
    return summary


def _write_eval_outputs(output_dir: Path, summary: Eval3DSummary) -> None:
    if output_dir is None:
        raise ValueError("output_dir must not be None.")
    if summary is None:
        raise ValueError("summary must not be None.")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "eval_3d.json"
    out_path.write_text(
        json.dumps(summary.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

