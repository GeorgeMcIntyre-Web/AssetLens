from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from ..domain.results_2d import Detection2D, SCHEMA_VERSION_2D


@dataclass(frozen=True)
class GtMask:
    image_name: str
    label: str
    bbox: tuple[int, int, int, int]
    mask_indices: list[int]
    mask_width: int
    mask_height: int


class PerLabelMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    mean_iou: float = Field(0.0, ge=0.0, le=1.0)
    precision_at_50: float = Field(0.0, ge=0.0, le=1.0)
    recall_at_50: float = Field(0.0, ge=0.0, le=1.0)
    f1_at_50: float = Field(0.0, ge=0.0, le=1.0)
    tp: int = Field(0, ge=0)
    fp: int = Field(0, ge=0)
    fn: int = Field(0, ge=0)


class TwoDImageDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    run_id: str
    image_path: str
    mean_iou: float
    precision_at_50: float
    recall_at_50: float
    f1_at_50: float


class TwoDEvalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    run_id: str
    mean_iou: float = Field(0.0, ge=0.0, le=1.0)
    precision_at_50: float = Field(0.0, ge=0.0, le=1.0)
    recall_at_50: float = Field(0.0, ge=0.0, le=1.0)
    f1_at_50: float = Field(0.0, ge=0.0, le=1.0)
    num_images: int = Field(0, ge=0)
    per_label: list[PerLabelMetrics] = Field(default_factory=list)


def _load_labels(path: Path) -> dict[str, list[dict]]:
    if path is None:
        raise ValueError("labels path must not be None.")
    if path.exists() is not True:
        raise FileNotFoundError(f"labels file not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) is not True:
        raise ValueError("labels JSON root must be an object.")

    images = raw.get("images")
    if images is None:
        images = raw
    if isinstance(images, dict) is not True:
        raise ValueError("labels images field must be an object.")

    out: dict[str, list[dict]] = {}
    for image_name, dets in images.items():
        if isinstance(dets, list) is not True:
            raise ValueError(f"labels for {image_name} must be a list.")
        out[image_name] = dets
    return out


def _parse_gt_list(image_name: str, dets: list[dict]) -> list[GtMask]:
    if image_name is None:
        raise ValueError("image_name must not be None.")
    if dets is None:
        raise ValueError("dets must not be None.")

    out: list[GtMask] = []
    for obj in dets:
        if isinstance(obj, dict) is not True:
            raise ValueError(f"ground truth item must be an object for {image_name}")
        label = obj.get("label")
        if label is None:
            raise ValueError(f"ground truth label missing for {image_name}")

        bbox = obj.get("bbox", [0, 0, 0, 0])
        if isinstance(bbox, list) is not True:
            raise ValueError(f"ground truth bbox must be a list for {image_name}")
        if len(bbox) != 4:
            raise ValueError(f"ground truth bbox must have 4 ints for {image_name}")

        indices = obj.get("mask_indices", [])
        if isinstance(indices, list) is not True:
            raise ValueError(f"ground truth mask_indices must be a list for {image_name}")

        mask_w = int(obj.get("mask_width", 0))
        mask_h = int(obj.get("mask_height", 0))
        if mask_w < 1:
            raise ValueError(f"ground truth mask_width missing/invalid for {image_name}")
        if mask_h < 1:
            raise ValueError(f"ground truth mask_height missing/invalid for {image_name}")

        out.append(
            GtMask(
                image_name=image_name,
                label=str(label),
                bbox=(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])),
                mask_indices=[int(x) for x in indices],
                mask_width=mask_w,
                mask_height=mask_h,
            )
        )
    return out


def _indices_to_mask(indices: list[int], width: int, height: int) -> np.ndarray:
    if indices is None:
        raise ValueError("indices must not be None.")
    if width < 1:
        raise ValueError("width must be one or greater.")
    if height < 1:
        raise ValueError("height must be one or greater.")

    mask = np.zeros((height, width), dtype=bool)
    if indices:
        flat = np.array(indices, dtype=int)
        valid = flat[(flat >= 0) & (flat < width * height)]
        mask.ravel()[valid] = True
    return mask


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    if a is None:
        raise ValueError("mask a must not be None.")
    if b is None:
        raise ValueError("mask b must not be None.")

    inter = float(np.logical_and(a, b).sum())
    union = float(np.logical_or(a, b).sum())
    if union == 0.0:
        return 0.0
    return float(inter / union)


def _safe_div(num: float, den: float) -> float:
    if den == 0.0:
        return 0.0
    return float(num / den)


def _match_and_score(pred_masks: list[np.ndarray], gt_masks: list[np.ndarray]) -> tuple[list[float], int, int, int]:
    if pred_masks is None:
        raise ValueError("pred_masks must not be None.")
    if gt_masks is None:
        raise ValueError("gt_masks must not be None.")

    if pred_masks:
        pass
    if not pred_masks:
        return [], 0, 0, len(gt_masks)

    if gt_masks:
        pass
    if not gt_masks:
        return [], 0, len(pred_masks), 0

    unmatched_gt = set(range(len(gt_masks)))
    ious: list[float] = []
    tp = 0
    fp = 0

    for pred in pred_masks:
        best_iou = 0.0
        best_j: int | None = None
        for j in list(unmatched_gt):
            v = _iou(pred, gt_masks[j])
            if v > best_iou:
                best_iou = v
                best_j = j
        if best_j is not None:
            if best_iou >= 0.50:
                tp += 1
                ious.append(best_iou)
                unmatched_gt.remove(best_j)
                continue
        fp += 1

    fn = len(unmatched_gt)
    return ious, tp, fp, fn


def _group_predictions(detections: list[Detection2D]) -> dict[str, list[Detection2D]]:
    if detections is None:
        raise ValueError("detections must not be None.")

    out: dict[str, list[Detection2D]] = {}
    for d in detections:
        image_name = Path(d.image_path).name
        if image_name not in out:
            out[image_name] = []
        out[image_name].append(d)
    return out


def evaluate_2d(labels_path: Path, detections: list[Detection2D], output_dir: Path) -> TwoDEvalSummary:
    if labels_path is None:
        raise ValueError("labels_path must not be None.")
    if detections is None:
        raise ValueError("detections must not be None.")
    if output_dir is None:
        raise ValueError("output_dir must not be None.")

    if detections:
        pass
    if not detections:
        raise ValueError("detections must not be empty.")

    labels_by_image = _load_labels(labels_path)
    pred_by_image = _group_predictions(detections)
    image_names = sorted(labels_by_image.keys())

    if image_names:
        pass
    if not image_names:
        raise ValueError("labels file contains no images.")

    run_id = detections[0].run_id
    overall_ious: list[float] = []
    overall_tp = 0
    overall_fp = 0
    overall_fn = 0
    per_label_acc: dict[str, dict[str, object]] = {}
    details: list[TwoDImageDetail] = []

    for image_name in image_names:
        if image_name not in pred_by_image:
            raise ValueError(f"Missing prediction for labelled image: {image_name}")

        gt_list = _parse_gt_list(image_name, labels_by_image[image_name])
        pred_list = pred_by_image[image_name]

        labels_set = {g.label for g in gt_list} | {p.label for p in pred_list}
        labels_sorted = sorted(labels_set)

        image_tp = 0
        image_fp = 0
        image_fn = 0
        image_ious: list[float] = []

        for label in labels_sorted:
            gt_for_label = [g for g in gt_list if g.label == label]
            pred_for_label = [p for p in pred_list if p.label == label]

            gt_masks = [
                _indices_to_mask(g.mask_indices, g.mask_width, g.mask_height) for g in gt_for_label
            ]
            pred_masks = [
                _indices_to_mask(p.mask_indices, p.mask_width, p.mask_height) for p in pred_for_label
            ]

            ious, tp, fp, fn = _match_and_score(pred_masks=pred_masks, gt_masks=gt_masks)

            image_ious.extend(ious)
            image_tp += tp
            image_fp += fp
            image_fn += fn

            if label not in per_label_acc:
                per_label_acc[label] = {"ious": [], "tp": 0, "fp": 0, "fn": 0}

            per_label_acc[label]["ious"].extend(ious)
            per_label_acc[label]["tp"] = int(per_label_acc[label]["tp"]) + tp
            per_label_acc[label]["fp"] = int(per_label_acc[label]["fp"]) + fp
            per_label_acc[label]["fn"] = int(per_label_acc[label]["fn"]) + fn

        mean_iou_img = _safe_div(sum(image_ious), float(len(image_ious)))
        prec_img = _safe_div(float(image_tp), float(image_tp + image_fp))
        rec_img = _safe_div(float(image_tp), float(image_tp + image_fn))
        f1_img = _safe_div(2.0 * prec_img * rec_img, prec_img + rec_img)

        details.append(
            TwoDImageDetail(
                schema_version=SCHEMA_VERSION_2D,
                run_id=run_id,
                image_path=image_name,
                mean_iou=mean_iou_img,
                precision_at_50=prec_img,
                recall_at_50=rec_img,
                f1_at_50=f1_img,
            )
        )

        overall_ious.extend(image_ious)
        overall_tp += image_tp
        overall_fp += image_fp
        overall_fn += image_fn

    mean_iou = _safe_div(sum(overall_ious), float(len(overall_ious)))
    precision = _safe_div(float(overall_tp), float(overall_tp + overall_fp))
    recall = _safe_div(float(overall_tp), float(overall_tp + overall_fn))
    f1 = _safe_div(2.0 * precision * recall, precision + recall)

    per_label_metrics: list[PerLabelMetrics] = []
    for label in sorted(per_label_acc.keys()):
        acc = per_label_acc[label]
        ious = list(acc["ious"])
        tp = int(acc["tp"])
        fp = int(acc["fp"])
        fn = int(acc["fn"])

        mean_iou_l = _safe_div(sum(ious), float(len(ious)))
        prec_l = _safe_div(float(tp), float(tp + fp))
        rec_l = _safe_div(float(tp), float(tp + fn))
        f1_l = _safe_div(2.0 * prec_l * rec_l, prec_l + rec_l)

        per_label_metrics.append(
            PerLabelMetrics(
                label=label,
                mean_iou=mean_iou_l,
                precision_at_50=prec_l,
                recall_at_50=rec_l,
                f1_at_50=f1_l,
                tp=tp,
                fp=fp,
                fn=fn,
            )
        )

    summary = TwoDEvalSummary(
        schema_version=SCHEMA_VERSION_2D,
        run_id=run_id,
        mean_iou=mean_iou,
        precision_at_50=precision,
        recall_at_50=recall,
        f1_at_50=f1,
        num_images=len(image_names),
        per_label=per_label_metrics,
    )

    _write_eval_outputs(output_dir=output_dir, summary=summary, details=details)
    return summary


def _write_eval_outputs(output_dir: Path, summary: TwoDEvalSummary, details: list[TwoDImageDetail]) -> None:
    if output_dir is None:
        raise ValueError("output_dir must not be None.")
    if summary is None:
        raise ValueError("summary must not be None.")
    if details is None:
        raise ValueError("details must not be None.")

    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "eval_2d.json"
    summary_path.write_text(
        json.dumps(summary.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    details_path = output_dir / "eval_2d_details.jsonl"
    with details_path.open("w", encoding="utf-8") as f:
        for d in details:
            f.write(json.dumps(d.model_dump(), sort_keys=True) + "\n")
