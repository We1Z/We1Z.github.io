"""
Murmuration — Unreal-side VAT importer & material builder
==========================================================

An original demo by Wei Zeng. Consumes the header/textures/mesh produced by
murmur_baker.py (plain Python, outside the editor) and finishes the job inside
Unreal:

  1. Imports Pos + Dir 16-bit VAT textures with VAT-safe settings
     (sRGB off, clamped, no mipmaps, lossless compression)
  2. Imports the card mesh OBJ
 3. Creates a Material whose graph decodes the bake:
        UV = (vertex.u, Frame/(frames-1))
        WPO = bounds_min + PosTex.rgb * bounds_size
        Emissive = DirTex.rgb * 0.2      (heading tint — visible playback sanity)
  4. Creates a MaterialInstanceConstant with Frame=0, ready for a Timeline
     or Blueprint to drive per-frame and loop.

Safe by default: runs a dry-run plan without touching the project.

------------------------------------------------------------------------------
RUN INSIDE UNREAL EDITOR (Python Editor Script Plugin enabled)
------------------------------------------------------------------------------
    py ue_import_vat.py --header baked/VAT_Murmuration_Header.json
    py ue_import_vat.py --header baked/VAT_Murmuration_Header.json --commit

The bake folder can sit anywhere; texture/mesh paths in the header are
relative to the header file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import unreal
except ImportError:
    unreal = None


# --------------------------------------------------------------------------- #
#  Planning
# --------------------------------------------------------------------------- #

def log(msg: str) -> None:
    (unreal.log if unreal else print)(msg)


def plan(header: dict, header_dir: str, dest: str) -> list[dict]:
    t = header["texture"]
    pos = header["position"]
    d = header["direction"]
    frames = header["frame_count"]
    return [
        {"do": "import_texture", "src": os.path.join(header_dir, pos["texture"]),
         "name": "T_VAT_Murmuration_Pos",
         "note": "16-bit · sRGB=off · clamp · no mips"},
        {"do": "import_texture", "src": os.path.join(header_dir, d["texture"]),
         "name": "T_VAT_Murmuration_Dir",
         "note": "16-bit · sRGB=off · clamp · no mips"},
        {"do": "import_mesh", "src": os.path.join(header_dir, header["mesh"]),
         "name": "SM_VAT_Murmuration", "note": f'{header["agent_count"]} cards'},
        {"do": "material", "name": "M_VAT_Murmuration",
         "note": f"UV(u, Frame/{frames - 1}) → WPO decode + heading emissive"},
        {"do": "material_instance", "name": "MI_VAT_Murmuration", "note": "Frame=0"},
        {"do": "assign", "mesh": "SM_VAT_Murmuration", "material": "M_VAT_Murmuration"},
        {"do": "save", "dir": dest},
    ]


# --------------------------------------------------------------------------- #
#  Execution
# --------------------------------------------------------------------------- #

def execute(header: dict, header_dir: str, dest: str) -> list[str]:
    eal = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(msg)
        unreal.log_error(msg)

    if not eal.does_directory_exist(dest):
        eal.make_directory(dest)

    # -- textures ----------------------------------------------------------- #
    def import_texture(src: str, name: str):
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", os.path.abspath(src))
        task.set_editor_property("destination_path", dest)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", False)
        task.set_editor_property("replace_existing", True)
        tools.import_asset_tasks([task])
        tex = eal.load_asset(f"{dest}/{name}")
        if tex is None:
            fail(f"texture import failed: {src}")
            return None
        # VAT settings: data, not color — no gamma, no mips, clamp edges.
        try:
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("address_x", unreal.TextureAddress.CLAMP)
            tex.set_editor_property("address_y", unreal.TextureAddress.CLAMP)
            tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NoMipmaps)
            tex.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP)
        except Exception as exc:
            log(f"  ! some texture settings unavailable on this API: {exc}")
        eal.save_asset(tex.get_path_name())
        return tex

    pos_tex = import_texture(os.path.join(header_dir, header["position"]["texture"]),
                             "T_VAT_Murmuration_Pos")
    dir_tex = import_texture(os.path.join(header_dir, header["direction"]["texture"]),
                             "T_VAT_Murmuration_Dir")

    # -- mesh --------------------------------------------------------------- #
    mesh_task = unreal.AssetImportTask()
    mesh_task.set_editor_property("filename",
                                  os.path.abspath(os.path.join(header_dir, header["mesh"])))
    mesh_task.set_editor_property("destination_path", dest)
    mesh_task.set_editor_property("destination_name", "SM_VAT_Murmuration")
    mesh_task.set_editor_property("automated", True)
    mesh_task.set_editor_property("save", True)
    mesh_task.set_editor_property("replace_existing", True)
    tools.import_asset_tasks([mesh_task])
    mesh = eal.load_asset(f"{dest}/SM_VAT_Murmuration")
    if mesh is None:
        fail("mesh import failed")

    # -- material graph ----------------------------------------------------- #
    mat_path = f"{dest}/M_VAT_Murmuration"
    if eal.does_asset_exist(mat_path):
        eal.delete_asset(mat_path)
    mat = tools.create_asset("M_VAT_Murmuration", dest,
                             unreal.Material, unreal.MaterialFactoryNew())

    frames = header["frame_count"]
    lo = header["position"]["bounds_min_cm"]
    size = header["position"]["bounds_size_cm"]
    Y = -160  # row cursor for readable node layout

    def add(cls, x, y):
        return mel.add_material_expression(mat, cls, x, y)

    # Frame scalar parameter -> Frame/(frames-1)
    frame_p = add(unreal.MaterialExpressionScalarParameter, -700, Y)
    frame_p.set_editor_property("parameter_name", "Frame")
    frame_p.set_editor_property("default_value", 0.0)
    denom = add(unreal.MaterialExpressionConstant, -700, Y + 70)
    denom.set_editor_property("r", float(frames - 1))
    fdiv = add(unreal.MaterialExpressionDivide, -500, Y)

    # UV = (vertex UV.x, normalized frame)
    texcoord = add(unreal.MaterialExpressionTextureCoordinate, -700, Y + 220)
    append = add(unreal.MaterialExpressionAppendVector, -300, Y)

    # Textures
    pos_sample = add(unreal.MaterialExpressionTextureSample, -80, Y - 40)
    pos_sample.set_editor_property("texture", pos_tex)
    dir_sample = add(unreal.MaterialExpressionTextureSample, -80, Y + 220)
    dir_sample.set_editor_property("texture", dir_tex)

    # Decode: bounds_min + pos.rgb * bounds_size
    size3 = add(unreal.MaterialExpressionConstant3Vector, 160, Y + 60)
    size3.set_editor_property("constant_value", unreal.LinearColor(*size))
    mul = add(unreal.MaterialExpressionMultiply, 360, Y)
    min3 = add(unreal.MaterialExpressionConstant3Vector, 160, Y + 200)
    min3.set_editor_property("constant_value", unreal.LinearColor(*lo))
    addpos = add(unreal.MaterialExpressionAdd, 560, Y)

    # Heading tint: dir.rgb * 0.2 -> emissive
    glow_k = add(unreal.MaterialExpressionConstant, 160, Y + 360)
    glow_k.set_editor_property("r", 0.2)
    glow = add(unreal.MaterialExpressionMultiply, 360, Y + 260)

    links = [
        (frame_p, "", fdiv, "A"),
        (denom, "", fdiv, "B"),
        (texcoord, "", append, "A"),
        (fdiv, "", append, "B"),
        (append, "", pos_sample, "UVs"),
        (append, "", dir_sample, "UVs"),
        (pos_sample, "", mul, "A"),
        (size3, "", mul, "B"),
        (mul, "", addpos, "A"),
        (min3, "", addpos, "B"),
        (dir_sample, "", glow, "A"),
        (glow_k, "", glow, "B"),
    ]
    for src, out, dst, inp in links:
        if not mel.connect_material_expressions(src, out, dst, inp):
            fail(f"material link failed: {type(src).__name__}.{out or '*'} → {inp}")

    mel.connect_material_property(addpos, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mel.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    eal.save_asset(mat_path)

    # -- material instance -------------------------------------------------- #
    mi_path = f"{dest}/MI_VAT_Murmuration"
    if eal.does_asset_exist(mi_path):
        eal.delete_asset(mi_path)
    mi = tools.create_asset("MI_VAT_Murmuration", dest,
                            unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, mat)
    eal.save_asset(mi_path)

    # -- assign to imported mesh (best-effort; API spelling moves between UE versions)
    if mesh is not None:
        try:
            subsys = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            subsys.set_material(mesh, [mat])  # one slot for the card mesh
            eal.save_asset(mesh.get_path_name())
            log("  assigned material via StaticMeshEditorSubsystem")
        except Exception as exc:
            log(f"  ! auto-assign skipped ({exc}); set M_VAT_Murmuration on SM slot 0 manually")

    eal.save_directory(dest, only_if_is_dirty=True, recursive=True)
    return errors


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Murmuration — in-UE VAT importer (demo)")
    ap.add_argument("--header", required=True, help="VAT_Murmuration_Header.json path")
    ap.add_argument("--dest", default="/Game/Murmuration", help="UE content destination")
    ap.add_argument("--commit", dest="commit", action="store_true",
                    help="actually import/build (default: dry-run)")
    args = ap.parse_args(argv)

    with open(args.header, "r", encoding="utf-8") as fh:
        header = json.load(fh)
    header_dir = os.path.dirname(os.path.abspath(args.header))

    steps = plan(header, header_dir, args.dest)
    mode = "COMMIT" if (args.commit and unreal) else "DRY-RUN"
    log(f"=== Murmuration VAT import — {mode} ===")
    for i, s in enumerate(steps, 1):
        target = (s.get("name") or s.get("src") or s.get("dir")
                  or f"{s.get('mesh', '')} ← {s.get('material', '')}")
        log(f"[{i}] {s['do']:18} {target}  {s.get('note', '')}")

    if args.commit and unreal is None:
        print("ERROR: --commit requires the Unreal editor Python environment", file=sys.stderr)
        return 2
    if not args.commit:
        log("Dry-run — add --commit inside the editor to execute.")
        return 0

    errors = execute(header, header_dir, args.dest)
    log(f"Done at {datetime.now():%H:%M:%S} — {len(errors)} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
