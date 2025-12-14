from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import typer

from .config.assembly_rules import default_assembly_rules
from .config.config import load_3d_config
from .eval.evaluation_3d import evaluate_3d
from .pipelines.assembly_graph_builder import build_assembly_graph, write_assembly_graph
from .pipelines.bom_builder import bom_from_assembly_graph
from .pipelines.pipeline_3d_dataset import convert_asset_id_images_to_labels, write_meta_json
from .pipelines.pipeline_3d_parts import run_3d_batch


app = typer.Typer(no_args_is_help=True)


@app.command("run")
def run_cmd(config: Path = typer.Option(..., "--config")) -> None:
    cfg = load_3d_config(config)
    outputs = run_3d_batch(cfg)
    typer.echo(f"OK: ran 3D pipeline for {outputs.summary.num_models} models")


@app.command("eval")
def eval_cmd(
    config: Path = typer.Option(..., "--config"),
    labels: Path = typer.Option(..., "--labels"),
) -> None:
    cfg = load_3d_config(config)
    outputs = run_3d_batch(cfg)
    summary = evaluate_3d(labels_path=labels, models=outputs.models, output_dir=cfg.output_dir)
    typer.echo(
        f"OK: count_acc={summary.count_accuracy:.3f} precision={summary.precision:.3f} recall={summary.recall:.3f} f1={summary.f1:.3f}"
    )


def _get_blender_exe() -> str:
    exe_env = os.environ.get("BLENDER_BIN")
    if exe_env:
        p = Path(exe_env)
        if p.exists() is not True:
            raise FileNotFoundError(f"BLENDER_BIN not found: {p}")
        return str(p)

    exe_env = os.environ.get("ASSETLENS_BLENDER_EXE")
    if exe_env:
        p = Path(exe_env)
        if p.exists() is not True:
            raise FileNotFoundError(f"ASSETLENS_BLENDER_EXE not found: {p}")
        return str(p)

    on_path = shutil.which("blender")
    if on_path:
        return on_path

    raise RuntimeError(
        "Blender executable not found. Install Blender and set BLENDER_BIN (or ASSETLENS_BLENDER_EXE) to its path."
    )


def _find_blender_script() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "scripts" / "blender" / "render_glb_dataset.py"
        if cand.exists():
            return cand
    raise FileNotFoundError(
        "Blender script not found at scripts/blender/render_glb_dataset.py. Run from the source repo."
    )


def _find_glbs(glb_arg: str) -> list[Path]:
    if glb_arg is None:
        raise ValueError("glb must not be None.")

    p = Path(glb_arg)
    if p.exists() is not True:
        raise FileNotFoundError(f"GLB path not found: {p}")

    if p.is_file():
        if p.suffix.lower() != ".glb":
            raise ValueError(f"Expected a .glb file, got: {p}")
        return [p]

    if p.is_dir():
        glbs = [x for x in p.glob("*.glb") if x.is_file()]
        glbs.sort()
        if glbs:
            return glbs
        raise RuntimeError(f"No .glb files found in directory: {p}")

    raise ValueError(f"GLB path must be a file or directory: {p}")


def _run_blender_render(
    blender_exe: str,
    script_path: Path,
    glb_path: Path,
    asset_out_dir: Path,
    views: int,
    res: int,
    seed: int,
) -> None:
    if blender_exe is None:
        raise ValueError("blender_exe must not be None.")
    if script_path is None:
        raise ValueError("script_path must not be None.")
    if glb_path is None:
        raise ValueError("glb_path must not be None.")
    if asset_out_dir is None:
        raise ValueError("asset_out_dir must not be None.")

    cmd = [
        blender_exe,
        "--background",
        "--python",
        str(script_path),
        "--",
        "--glb",
        str(glb_path),
        "--out",
        str(asset_out_dir),
        "--views",
        str(int(views)),
        "--res",
        str(int(res)),
        "--seed",
        str(int(seed)),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return

    stderr = proc.stderr.strip()
    stdout = proc.stdout.strip()
    msg = "Blender render failed."
    if stderr:
        msg = msg + f"\nSTDERR:\n{stderr}"
    if stdout:
        msg = msg + f"\nSTDOUT:\n{stdout}"
    raise RuntimeError(msg)


@app.command("dataset")
def dataset_cmd(
    glb: str = typer.Option(..., "--glb"),
    out: Path = typer.Option(..., "--out"),
    views: int = typer.Option(12, "--views"),
    res: int = typer.Option(1024, "--res"),
    seed: int = typer.Option(0, "--seed"),
) -> None:
    if out is None:
        raise ValueError("--out must not be None.")
    if views < 1:
        raise ValueError("--views must be one or greater.")
    if res < 8:
        raise ValueError("--res must be 8 or greater.")
    if seed < 0:
        raise ValueError("--seed must be zero or greater.")

    blender_exe = _get_blender_exe()
    script_path = _find_blender_script()
    glb_paths = _find_glbs(glb)

    out.mkdir(parents=True, exist_ok=True)

    for glb_path in glb_paths:
        asset_name = glb_path.stem
        asset_out_dir = out / asset_name
        asset_out_dir.mkdir(parents=True, exist_ok=True)

        _run_blender_render(
            blender_exe=blender_exe,
            script_path=script_path,
            glb_path=glb_path,
            asset_out_dir=asset_out_dir,
            views=views,
            res=res,
            seed=seed,
        )

        id_dir = asset_out_dir / "images_id"
        rgb_dir = asset_out_dir / "images_rgb"
        if id_dir.exists() is not True:
            raise RuntimeError(f"images_id missing after render: {id_dir}")
        if rgb_dir.exists() is not True:
            raise RuntimeError(f"images_rgb missing after render: {rgb_dir}")

        mapping_path = asset_out_dir / "color_to_part.json"
        if mapping_path.exists() is not True:
            raise RuntimeError(f"color_to_part.json missing after render: {mapping_path}")

        scene_graph_path = asset_out_dir / "scene_graph.json"
        if scene_graph_path.exists() is not True:
            raise RuntimeError(f"scene_graph.json missing after render: {scene_graph_path}")

        convert_asset_id_images_to_labels(asset_dir=asset_out_dir)
        write_meta_json(glb_path=glb_path, asset_dir=asset_out_dir, seed=seed, views=views, res=res)

    typer.echo(f"OK: rendered dataset for {len(glb_paths)} GLB assets to {out}")


@app.command("bom")
def bom_cmd(
    renders: Path = typer.Option(..., "--renders"),
    out: Path = typer.Option(..., "--out"),
) -> None:
    if renders is None:
        raise ValueError("--renders must not be None.")
    if out is None:
        raise ValueError("--out must not be None.")
    if renders.exists() is not True:
        raise FileNotFoundError(f"renders directory not found: {renders}")

    asset_dirs = [p for p in renders.iterdir() if p.is_dir()]
    asset_dirs.sort(key=lambda p: p.name)

    if asset_dirs:
        pass
    if not asset_dirs:
        raise RuntimeError(f"No asset folders found under renders directory: {renders}")

    rules = default_assembly_rules()
    out.mkdir(parents=True, exist_ok=True)

    total_parts: set[str] = set()
    total_lines = 0

    for asset_dir in asset_dirs:
        scene_graph_path = asset_dir / "scene_graph.json"
        meta_path = asset_dir / "meta.json"
        if scene_graph_path.exists() is not True:
            raise FileNotFoundError(f"scene_graph.json missing for asset: {scene_graph_path}")
        if meta_path.exists() is not True:
            raise FileNotFoundError(f"meta.json missing for asset: {meta_path}")

        graph = build_assembly_graph(scene_graph_path=scene_graph_path, rules=rules)

        asset_out_dir = out / asset_dir.name
        asset_out_dir.mkdir(parents=True, exist_ok=True)

        write_assembly_graph(output_path=asset_out_dir / "assembly_graph.json", graph=graph)

        bom = bom_from_assembly_graph(
            graph=graph,
            rules=rules,
            asset_id=asset_dir.name,
            scene_graph_path=scene_graph_path,
            meta_path=meta_path,
        )

        bom_path = asset_out_dir / "bom_3d.json"
        bom_path.write_text(
            json.dumps(bom.model_dump(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        total_lines += len(bom.lines)
        for line in bom.lines:
            total_parts.add(line.part_name)

    typer.echo(
        f"OK: processed {len(asset_dirs)} assets, unique_parts={len(total_parts)}, total_lines={total_lines}"
    )
