from __future__ import annotations

import json
from pathlib import Path

from ..config.config import AssetLens2DConfig
from ..config.logging_utils import get_logger
from ..domain.results_2d import Detection2D, Run2DOutputs, Run2DSummary
from ..sam_wrappers.sam2d_runner import FakeSamRunner, MaskResult
from .bom_builder import build_bom_from_2d, write_bom


log = get_logger("assetlens.pipeline_2d")


def _find_images(dataset_dir: Path, image_glob: str) -> list[Path]:
    if dataset_dir is None:
        raise ValueError("dataset_dir must not be None.")
    if image_glob is None:
        raise ValueError("image_glob must not be None.")
    if dataset_dir.exists() is not True:
        raise FileNotFoundError(f"dataset_dir not found: {dataset_dir}")

    paths = [p for p in dataset_dir.glob(image_glob) if p.is_file()]
    paths.sort()
    return paths


def _infer_size(image_path: Path, fallback_w: int, fallback_h: int) -> tuple[int, int]:
    if image_path is None:
        raise ValueError("image_path must not be None.")
    if fallback_w < 1:
        raise ValueError("fallback_w must be one or greater.")
    if fallback_h < 1:
        raise ValueError("fallback_h must be one or greater.")

    if image_path.exists() is not True:
        return fallback_w, fallback_h

    try:
        from PIL import Image

        with Image.open(image_path) as img:
            w, h = img.size
        if w > 0:
            if h > 0:
                return int(w), int(h)
    except Exception:
        pass

    return fallback_w, fallback_h


def _to_detections(masks: list[MaskResult], run_id: str) -> list[Detection2D]:
    if masks is None:
        raise ValueError("masks must not be None.")
    if run_id is None:
        raise ValueError("run_id must not be None.")

    out: list[Detection2D] = []
    for m in masks:
        out.append(
            Detection2D(
                run_id=run_id,
                image_path=m.image_path,
                label=m.label,
                score=m.score,
                bbox=m.bbox,
                mask_indices=m.mask_indices,
                mask_width=m.mask_width,
                mask_height=m.mask_height,
            )
        )
    return out


def _make_summary(run_id: str, images: list[Path], detections: list[Detection2D], labels: list[str]) -> Run2DSummary:
    if run_id is None:
        raise ValueError("run_id must not be None.")
    if images is None:
        raise ValueError("images must not be None.")
    if detections is None:
        raise ValueError("detections must not be None.")
    if labels is None:
        raise ValueError("labels must not be None.")

    counts: dict[str, int] = {}
    for label in sorted(set(labels)):
        counts[label] = 0

    for det in detections:
        if det.label not in counts:
            counts[det.label] = 0
        counts[det.label] += 1

    return Run2DSummary(
        run_id=run_id,
        num_images=len(images),
        num_detections=len(detections),
        counts_by_label=counts,
    )


def _write_outputs(output_dir: Path, summary: Run2DSummary, detections: list[Detection2D]) -> None:
    if output_dir is None:
        raise ValueError("output_dir must not be None.")
    if summary is None:
        raise ValueError("summary must not be None.")
    if detections is None:
        raise ValueError("detections must not be None.")

    ordered = sorted(detections, key=lambda d: (d.image_path, d.label, d.bbox))

    jsonl_path = output_dir / "run_2d.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for det in ordered:
            f.write(json.dumps(det.model_dump(), sort_keys=True) + "\n")

    summary_path = output_dir / "run_2d_summary.json"
    summary_path.write_text(
        json.dumps(summary.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    alias_path = output_dir / "run_2d.json"
    alias_path.write_text(
        json.dumps(summary.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    log.info(f"Wrote run_2d.jsonl and summaries to {output_dir}")


def run_2d_batch(config: AssetLens2DConfig) -> Run2DOutputs:
    if config is None:
        raise ValueError("config must not be None.")

    fake_cfg = config.fake_runner
    if fake_cfg.enabled is not True:
        raise RuntimeError("Only FakeSamRunner is supported in PoC++.")

    image_paths = _find_images(config.dataset_dir, config.image_glob)
    if image_paths:
        pass
    if not image_paths:
        raise RuntimeError(
            f"No dataset images found for dataset_dir={config.dataset_dir} glob={config.image_glob}"
        )

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = FakeSamRunner(max_instances_per_label=fake_cfg.max_instances_per_prompt)

    detections: list[Detection2D] = []
    for image_path in image_paths:
        w, h = _infer_size(image_path, fake_cfg.mask_width, fake_cfg.mask_height)
        masks = runner.run(
            image_path=str(image_path),
            labels=config.include_classes,
            width=w,
            height=h,
            seed=config.seed,
        )
        detections.extend(_to_detections(masks=masks, run_id=config.run_id))

    summary = _make_summary(
        run_id=config.run_id,
        images=image_paths,
        detections=detections,
        labels=config.include_classes,
    )
    _write_outputs(output_dir=output_dir, summary=summary, detections=detections)
    bom, _counts = build_bom_from_2d(detections=detections, assembly_id=f"2d:{config.run_id}")
    write_bom(output_path=output_dir / "bom_2d.json", assembly=bom)
    return Run2DOutputs(summary=summary, detections=detections)
