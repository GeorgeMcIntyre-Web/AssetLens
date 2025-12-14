# AssetLens-Core (PoC++)

## Overview

### What is AssetLens?
AssetLens turns CAD/GLB assemblies into a reproducible parts dataset and a draft bill of materials. Given one or more `.glb` files, it renders consistent turntable views, produces instance‑ID masks, converts those masks into per‑view labels, and runs a deterministic segmentation/counting pipeline over the images.

The result is a lightweight, repeatable baseline for “what parts exist, where are they, and how many are there?”—without requiring SAM or any heavy ML stack yet. Every stage is deterministic so you can trust diffs between runs.

AssetLens is for teams working with robotics cell assets: grippers, fixtures, tooling, safety hardware, and other process‑simulation assemblies. This repo is the core PoC pipeline that you can extend later with real segmentation backends and richer ontologies.

### Status / limitations
- Deterministic PoC. Fake runners are the default.
- Segmentation accuracy metrics are only meaningful once labels are real (Phase D labels are CAD‑derived).
- Inputs supported today: `.glb` assemblies and image folders.

## Five-minute quickstart (Windows)

1) Install in editable mode:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

2) Point AssetLens at Blender (new terminals required after `setx`):
```powershell
setx BLENDER_BIN "C:\Program Files\Blender Foundation\Blender\blender.exe"
```
Verify:
```powershell
& "$env:BLENDER_BIN" --version
```

3) Render a dataset from a GLB:
```powershell
assetlens3d dataset --glb "C:\path\to\asset.glb" --out poc_data\3d_renders --views 6 --res 1024 --seed 123
```

4) Run the 2D pipeline on the generated RGB images:
Edit `config_2d.yaml` to:
```yaml
dataset_dir: poc_data/3d_renders/<asset_name>
image_glob: images_rgb/view_*.png
labels_path: poc_data/3d_renders/<asset_name>/labels_2d.json
```
Then:
```powershell
assetlens2d run --config config_2d.yaml
assetlens2d eval --config config_2d.yaml --labels poc_data/3d_renders/<asset_name>/labels_2d.json
```

## Pipeline overview

```
GLB
  → Blender headless renders (RGB + ID)
    → color_to_part.json + scene_graph.json + meta.json
      → ID → labels_2d.json
        → 2D runner (Fake now / SAM later)
          → outputs/run_2d.jsonl + run_2d_summary.json
            → outputs/eval_2d.json + eval_2d_details.jsonl
              → outputs/bom_2d.json / bom_3d.json (draft)
```

### Why Blender?
- Headless rendering with fixed cameras and resolution.
- Instance‑ID pass gives stable segmentation IDs.
- Works directly from GLB without proprietary CAD APIs.
- Deterministic dataset generation for repeatable evals.

### BOM from geometry (no CAD metadata required)
AssetLens treats each mesh node in `scene_graph.json` as a part. Names are normalized deterministically (lowercase, trim, strip left/right and numeric suffixes), then categorized using `assetlens_core/config/assembly_rules.py` (exact/substring match first, then regex, then `unknown`). The semantic assembly graph is hashed to detect repeated subassemblies, then rolled into `bom_3d.json` with evidence node IDs and source meshes.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
assetlens2d --help
assetlens3d --help
```

## Blender setup

- Set `BLENDER_BIN` if Blender is not on `PATH`:
```powershell
setx BLENDER_BIN "C:\Program Files\Blender Foundation\Blender\blender.exe"
```
- Open a new terminal after running `setx`.
- Verify Blender:
```powershell
& "$env:BLENDER_BIN" --version
```
You can also use `ASSETLENS_BLENDER_EXE` as an override.

## Commands

### 2D PoC dataset (tiny, deterministic)
```powershell
python scripts\make_poc_2d_dataset.py --out poc_data\2d_cells --n 2 --seed 123
```

### Run 2D pipeline
```powershell
assetlens2d run --config config_2d.yaml
```

### Evaluate 2D results
```powershell
assetlens2d eval --config config_2d.yaml --labels poc_data\2d_cells\labels_2d.json
```

### Render GLB → 2D dataset
```powershell
assetlens3d dataset --glb "<path-or-dir>" --out poc_data\3d_renders --views 12 --res 1024 --seed 123
```

### Build semantic assembly BOM
```powershell
assetlens3d bom --renders poc_data\3d_renders --out outputs
```

### 3D PoC (fake parts runner)
```powershell
assetlens3d run --config config_3d.yaml
assetlens3d eval --config config_3d.yaml --labels poc_data\3d_cells\labels_3d.json
```

## Outputs

2D run writes under `outputs/`:
- `run_2d.jsonl` (one detection per line)
- `run_2d_summary.json` and `run_2d.json` (summary alias)
- `bom_2d.json`

2D eval writes under `outputs/`:
- `eval_2d.json` (aggregate metrics)
- `eval_2d_details.jsonl` (per‑image metrics)

3D dataset generation writes per asset under `poc_data/3d_renders/<asset_name>/`:
- `images_rgb/view_###.png`
- `images_id/view_###.png`
- `color_to_part.json`
- `camera_metadata.json`
- `scene_graph.json`
- `labels_2d.json`
- `meta.json`

3D run/eval writes under `outputs/`:
- `run_3d.jsonl`, `run_3d_summary.json`
- `eval_3d.json`
- `bom_3d.json`

## Tests

```powershell
python -m pytest -q
```

## Troubleshooting

- `assetlens2d` / `assetlens3d` not recognized: re‑run `python -m pip install -e ".[dev]"` inside your venv and reopen the terminal.
- `BLENDER_BIN not set`: check `echo $env:BLENDER_BIN` (PowerShell) and re‑run `setx` if needed.
- Blender `TBBmalloc` warnings are usually safe if `--version` works.

## Roadmap
- Replace Fake runners with SAM / real segmentation backends.
- Expand part ontology + assembly rules for richer BOMs.
- Scale dataset generation (batching, caching, multi‑view presets).
- Export BOM to CSV/Excel and integrate Process Simulate metadata.
