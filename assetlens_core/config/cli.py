from __future__ import annotations

from pathlib import Path

import typer

from .config import load_2d_config
from ..eval.evaluation_2d import evaluate_2d
from ..pipelines.pipeline_2d_assets import run_2d_batch


app = typer.Typer(no_args_is_help=True)


@app.command("run")
def run_cmd(config: Path = typer.Option(..., "--config")) -> None:
    cfg = load_2d_config(config)
    outputs = run_2d_batch(cfg)
    typer.echo(f"OK: ran 2D pipeline for {outputs.summary.num_images} images")


@app.command("eval")
def eval_cmd(
    config: Path = typer.Option(..., "--config"),
    labels: Path = typer.Option(..., "--labels"),
) -> None:
    cfg = load_2d_config(config)
    outputs = run_2d_batch(cfg)
    summary = evaluate_2d(labels_path=labels, detections=outputs.detections, output_dir=cfg.output_dir)
    typer.echo(
        f"OK: mean_iou={summary.mean_iou:.3f} precision={summary.precision_at_50:.3f} recall={summary.recall_at_50:.3f} f1={summary.f1_at_50:.3f}"
    )


from ..cli_3d import app as assetlens3d_app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
