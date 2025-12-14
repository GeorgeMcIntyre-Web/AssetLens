from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" not in argv:
        raise ValueError("Expected Blender args separator '--'.")
    idx = argv.index("--")
    args = argv[idx + 1 :]

    parser = argparse.ArgumentParser()
    parser.add_argument("--glb", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--views", type=int, default=12)
    parser.add_argument("--res", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args(args)


def _stable_rand01(seed: int, key: str) -> float:
    digest = hashlib.sha256(f"{seed}|{key}".encode("utf-8")).digest()
    val = int.from_bytes(digest[:8], byteorder="little", signed=False)
    return float(val / 2**64)


def _generate_cameras(num_views: int, seed: int, radius: float) -> list[dict]:
    if num_views < 1:
        raise ValueError("views must be one or greater.")

    rings = [0.0]
    if num_views >= 3:
        rings = [0.0, 20.0, -20.0]

    elev_jitter = (_stable_rand01(seed, "elev_base") - 0.5) * 5.0
    step = 2.0 * math.pi / float(num_views)

    cams = []
    for i in range(num_views):
        az = step * float(i)
        jitter = (_stable_rand01(seed, f"az|{i}") - 0.5) * step * 0.1
        az = az + jitter

        elev_deg = rings[i % len(rings)] + elev_jitter
        elev_rad = math.radians(elev_deg)

        x = radius * math.cos(az) * math.cos(elev_rad)
        y = radius * math.sin(az) * math.cos(elev_rad)
        z = radius * math.sin(elev_rad)

        cams.append(
            {
                "name": f"view_{i:03d}",
                "position": [float(x), float(y), float(z)],
                "look_at": [0.0, 0.0, 0.0],
                "fov_deg": 50.0,
            }
        )
    return cams


def _clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _import_glb(path: Path) -> None:
    bpy.ops.import_scene.gltf(filepath=str(path))


def _get_mesh_objects() -> list[bpy.types.Object]:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    meshes.sort(key=lambda o: o.name)
    if meshes:
        return meshes
    raise RuntimeError("No mesh parts found in GLB.")


def _make_emission_material(name: str, rgb: tuple[int, int, int]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new(type="ShaderNodeOutputMaterial")
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = (
        rgb[0] / 255.0,
        rgb[1] / 255.0,
        rgb[2] / 255.0,
        1.0,
    )
    emission.inputs["Strength"].default_value = 1.0
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def _assign_unique_colors(meshes: list[bpy.types.Object], seed: int) -> tuple[dict[str, tuple[int, int, int]], dict[str, bpy.types.Material]]:
    rng = random.Random(int(seed))
    used: set[tuple[int, int, int]] = set()
    colors: dict[str, tuple[int, int, int]] = {}
    id_mats: dict[str, bpy.types.Material] = {}

    for obj in meshes:
        rgb = (0, 0, 0)
        while rgb == (0, 0, 0) or rgb in used:
            rgb = (rng.randint(1, 254), rng.randint(1, 254), rng.randint(1, 254))
        used.add(rgb)
        colors[obj.name] = rgb
        id_mats[obj.name] = _make_emission_material(f"id_{obj.name}", rgb)

    return colors, id_mats


def _capture_original_materials(meshes: list[bpy.types.Object]) -> dict[str, list[bpy.types.Material | None]]:
    out: dict[str, list[bpy.types.Material | None]] = {}
    for obj in meshes:
        mats: list[bpy.types.Material | None] = []
        for slot in obj.material_slots:
            mats.append(slot.material)
        out[obj.name] = mats
    return out


def _restore_materials(meshes: list[bpy.types.Object], originals: dict[str, list[bpy.types.Material | None]]) -> None:
    for obj in meshes:
        mats = originals.get(obj.name, [])
        slots = obj.material_slots
        for i, slot in enumerate(slots):
            if i < len(mats):
                slot.material = mats[i]


def _assign_id_materials(meshes: list[bpy.types.Object], id_mats: dict[str, bpy.types.Material]) -> None:
    for obj in meshes:
        mat = id_mats[obj.name]
        if len(obj.material_slots) == 0:
            obj.data.materials.append(mat)
        for slot in obj.material_slots:
            slot.material = mat


def _setup_render(res: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = int(res)
    scene.render.resolution_y = int(res)
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"


def _ensure_light() -> None:
    bpy.ops.object.light_add(type="SUN", location=(5.0, 5.0, 5.0))
    light = bpy.context.active_object
    light.data.energy = 3.0


def _ensure_camera() -> bpy.types.Object:
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    return cam


def _point_camera(cam: bpy.types.Object, look_at: tuple[float, float, float]) -> None:
    direction = Vector(look_at) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_scene_graph(meshes: list[bpy.types.Object]) -> dict:
    nodes = []
    roots = []
    for obj in meshes:
        parent = None
        if obj.parent is not None:
            parent = obj.parent.name
        children = [c.name for c in obj.children if c.type == "MESH"]
        nodes.append({"name": obj.name, "parent": parent, "children": children})
        if parent is None:
            roots.append(obj.name)
    roots.sort()
    nodes.sort(key=lambda n: n["name"])
    return {"roots": roots, "nodes": nodes}


def main() -> None:
    args = _parse_args()
    glb_path = Path(args.glb)
    out_dir = Path(args.out)
    views = int(args.views)
    res = int(args.res)
    seed = int(args.seed)

    if glb_path.exists() is not True:
        raise FileNotFoundError(f"GLB not found: {glb_path}")
    if views < 1:
        raise ValueError("views must be one or greater.")
    if res < 8:
        raise ValueError("res must be 8 or greater.")
    if seed < 0:
        raise ValueError("seed must be zero or greater.")

    out_dir.mkdir(parents=True, exist_ok=True)
    rgb_dir = out_dir / "images_rgb"
    id_dir = out_dir / "images_id"
    rgb_dir.mkdir(parents=True, exist_ok=True)
    id_dir.mkdir(parents=True, exist_ok=True)

    _clear_scene()
    _import_glb(glb_path)

    meshes = _get_mesh_objects()
    colors, id_mats = _assign_unique_colors(meshes, seed=seed)
    originals = _capture_original_materials(meshes)

    _setup_render(res=res)
    _ensure_light()
    cam = _ensure_camera()

    cameras = _generate_cameras(num_views=views, seed=seed, radius=2.0)

    for cam_info in cameras:
        name = cam_info["name"]
        pos = cam_info["position"]
        look = cam_info["look_at"]
        cam.location = Vector(pos)
        _point_camera(cam, tuple(look))

        _restore_materials(meshes, originals)
        bpy.context.scene.render.filepath = str(rgb_dir / f"{name}.png")
        bpy.ops.render.render(write_still=True)

        _assign_id_materials(meshes, id_mats)
        bpy.context.scene.render.filepath = str(id_dir / f"{name}.png")
        bpy.ops.render.render(write_still=True)

    mapping = {}
    for obj_name, rgb in colors.items():
        hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        mapping[hex_color.lower()] = obj_name

    _write_json(out_dir / "color_to_part.json", mapping)
    _write_json(out_dir / "camera_metadata.json", cameras)
    _write_json(out_dir / "scene_graph.json", _build_scene_graph(meshes))


if __name__ == "__main__":
    main()

