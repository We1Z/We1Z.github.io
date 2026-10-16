"""
Relay — bidirectional Unreal ⇄ ShotGrid sync (demo)
===================================================

An original demo by Wei Zeng. Same shape as a production shotgun_api3
integration, running against a mock ShotGrid site:

  PULL  ShotGrid → Unreal:  sg.find("Shot", …) — active shots become
                              LevelSequences tagged with frames, SG status
                              code and assignees. updated_at stamps drive
                              change/conflict detection (ShotGrid wins).
  PUSH  Unreal → ShotGrid:  scans a content folder, reports Static/Skeletal
                              meshes via sg.create/update("Asset", …).
                              Idempotent — unchanged assets are skipped.

Mutations on ShotGrid appear in EventLogEntry automatically; engine-side
actions are appended to the local relay sync ledger. Dry-run by default.

Switching to a real site changes ONE line:
    sg = MockShotgun(site_file=...)   →   shotgun_api3.Shotgun(base_url, ...)
Nothing else in this file changes.

------------------------------------------------------------------------------
RUN
------------------------------------------------------------------------------
    python3 ue_relay.py --direction pull                 # plan, anywhere
    py ue_relay.py --site /path/sg_site.json --direction both --commit   # UE
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mock_shotgrid import MockShotgun, STATUS_LABELS  # noqa: E402
import relay_ledger  # noqa: E402

try:
    import unreal
except ImportError:
    unreal = None

SHOT_FIELDS = [
    "code", "sg_status_list", "sg_frame_in", "sg_frame_out", "updated_at",
    "sg_sequence.Sequence.code", "task_assignees",
]


# --------------------------------------------------------------------------- #
#  PULL — ShotGrid → Unreal LevelSequences
# --------------------------------------------------------------------------- #

def plan_pull(sg: MockShotgun, shots_root: str) -> list[dict]:
    eal = unreal.EditorAssetLibrary if unreal else None
    users = {u["id"]: u.get("name") or u.get("login") or str(u["id"])
             for u in sg.find("HumanUser", [], ["name", "login"])}

    shots = sg.find(
        "Shot",
        [["sg_status_list", "is_not", "omt"],
         ["sg_sequence.Sequence.sg_status_list", "is_not", "omt"]],
        SHOT_FIELDS,
        order=[{"field_name": "sg_sequence.Sequence.code", "direction": "asc"},
               {"field_name": "code", "direction": "asc"}])

    plan: list[dict] = []
    for s in shots:
        seq = s.get("sg_sequence.Sequence.code", "SQ???")
        shot_dir = f"{shots_root}/{seq}/{s['code']}"
        target = f"{shot_dir}/LS_{seq}_{s['code']}"
        entry = {"key": f"{seq}/{s['code']}", "target": target, "shot": s,
                 "assignees": [users.get(u["id"], str(u["id"]))
                               for u in s.get("task_assignees", [])]}

        if eal is None:
            entry.update(action="create", note="engine state unknown outside UE — planned")
            plan.append(entry)
            continue
        if not eal.does_asset_exist(target):
            entry.update(action="create", note="LevelSequence missing")
            plan.append(entry)
            continue

        asset = eal.load_asset(target)
        stamped = _get_meta(asset, "sg_updated_at")
        label = STATUS_LABELS.get(s["sg_status_list"], s["sg_status_list"])
        if not stamped:
            entry.update(action="update", note="existing sequence has no SG stamp")
        elif stamped == s["updated_at"]:
            entry.update(action="skip", note=f"in sync · {label}")
        elif stamped < s["updated_at"]:
            entry.update(action="update",
                         note=f"ShotGrid newer · {label} {s['sg_frame_in']}-{s['sg_frame_out']}")
        else:
            entry.update(action="conflict",
                         note="UE stamp newer than ShotGrid — SG wins, will overwrite")
        plan.append(entry)
    return plan


def execute_pull(sg: MockShotgun, plan: list[dict], shots_root: str,
                 ledger: str) -> int:
    eal = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    errors = 0

    for e in plan:
        s = e["shot"]
        seq = s.get("sg_sequence.Sequence.code", "SQ???")
        shot_dir = f"{shots_root}/{seq}/{s['code']}"
        name = f"LS_{seq}_{s['code']}"
        target = f"{shot_dir}/{name}"

        if e["action"] == "skip":
            relay_ledger.append(ledger, "pull", "shot", e["key"], "skip", "in sync")
            continue

        if not eal.does_directory_exist(shot_dir):
            eal.make_directory(shot_dir)

        if e["action"] == "create":
            asset = tools.create_asset(
                name, shot_dir, unreal.LevelSequence,
                unreal.LevelSequenceFactoryNew())
            if asset is None:
                unreal.log_error(f"PULL create failed: {target}")
                errors += 1
                continue
        else:  # update / conflict
            asset = eal.load_asset(target)
            if asset is None:
                unreal.log_error(f"PULL update failed (vanished?): {target}")
                errors += 1
                continue

        _set_meta_bulk(asset, {
            "sequence": seq,
            "shot": s["code"],
            "frame_in": str(s.get("sg_frame_in", "")),
            "frame_out": str(s.get("sg_frame_out", "")),
            "status": s.get("sg_status_list", ""),
            "assignee": ", ".join(e["assignees"]),
            "sg_updated_at": s["updated_at"],
        })
        eal.save_asset(target)
        detail = (f"{s['sg_status_list']} {s.get('sg_frame_in','')}-"
                  f"{s.get('sg_frame_out','')}")
        relay_ledger.append(ledger, "pull", "shot", e["key"], e["action"], detail)
        unreal.log(f"PULL  {e['action']:8} {e['key']} → {target}")
    return errors


# --------------------------------------------------------------------------- #
#  PUSH — Unreal meshes → ShotGrid Assets
# --------------------------------------------------------------------------- #

def plan_push(sg: MockShotgun, assets_root: str) -> list[dict]:
    eal = unreal.EditorAssetLibrary
    plan: list[dict] = []
    mesh_classes = {"StaticMesh": unreal.StaticMesh,
                    "SkeletalMesh": unreal.SkeletalMesh}
    try:
        sm_subsys = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    except Exception:
        sm_subsys = None

    for package in eal.list_assets(assets_root, recursive=True, include_folder=False):
        asset = eal.load_asset(package)
        if asset is None:
            continue
        asset_type = next((n for n, cls in mesh_classes.items()
                           if isinstance(asset, cls)), None)
        if asset_type is None:
            continue

        code = package.rsplit("/", 1)[-1]
        path = package.rsplit("/", 1)[0]
        lod = 0
        if asset_type == "StaticMesh" and sm_subsys is not None:
            try:
                lod = sm_subsys.get_lod_count(asset)
            except Exception:
                lod = 0

        existing = sg.find_one("Asset", [["code", "is", code]],
                               ["sg_asset_type", "sg_package_path", "sg_lod_count"])
        data = {"sg_asset_type": asset_type, "sg_package_path": path,
                "sg_lod_count": lod, "sg_status_list": "ip"}
        if (existing and existing.get("sg_asset_type") == asset_type
                and existing.get("sg_package_path") == path
                and (existing.get("sg_lod_count") or 0) == lod):
            action, note = "skip", "unchanged"
        else:
            action = "create" if existing is None else "update"
            note = f"{asset_type} · LOD {lod}"
        plan.append({"key": code, "action": action, "note": note,
                     "data": data, "sg_id": existing["id"] if existing else None})
    return plan


def execute_push(sg: MockShotgun, plan: list[dict], ledger: str) -> int:
    errors = 0
    for e in plan:
        if e["action"] == "skip":
            relay_ledger.append(ledger, "push", "asset", e["key"], "skip", "unchanged")
            continue
        try:
            if e["action"] == "create":
                sg.create("Asset", {"code": e["key"], **e["data"]})
            else:
                sg.update("Asset", e["sg_id"], e["data"])
            relay_ledger.append(ledger, "push", "asset", e["key"],
                                e["action"], e["note"])
            unreal.log(f"PUSH  {e['action']:8} {e['key']}  {e['note']}")
        except Exception as exc:
            unreal.log_error(f"PUSH failed {e['key']}: {exc}")
            errors += 1
    return errors


# --------------------------------------------------------------------------- #
#  Metadata helpers (API spellings shift across UE versions)
# --------------------------------------------------------------------------- #

def _get_meta(asset, key: str) -> str:
    eal = unreal.EditorAssetLibrary
    fn = getattr(eal, "get_metadata_tag", None)
    if fn:
        try:
            return fn(asset, key) or ""
        except Exception:
            return ""
    return ""


def _set_meta_bulk(asset, tags: dict) -> None:
    eal = unreal.EditorAssetLibrary
    for key, value in tags.items():
        try:
            if hasattr(eal, "set_metadata_tag"):
                eal.set_metadata_tag(asset, key, str(value))
            else:
                asset.set_metadata_tag(unreal.Name(key), str(value))
        except Exception as exc:
            unreal.log_warning(f"metadata {key} set failed: {exc}")


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def _print_plan(plan: list[dict]) -> None:
    counts: dict[str, int] = {}
    for e in plan:
        counts[e["action"]] = counts.get(e["action"], 0) + 1
        print(f"{e.get('direction', 'PULL'):4}  {e['action']:9} "
              f"{e['entity'] if 'entity' in e else 'shot':5} "
              f"{e['key']:24} {e.get('note', '')}")
    print("  plan summary:", counts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Relay — UE ⇄ ShotGrid sync (demo)")
    ap.add_argument("--site", default="sg_site.json", help="mock ShotGrid site JSON")
    ap.add_argument("--ledger", default="relay_sync_log.jsonl")
    ap.add_argument("--direction", choices=["pull", "push", "both"], default="both")
    ap.add_argument("--shots-root", default="/Game/Cinematics/Sequences")
    ap.add_argument("--assets-root", default="/Game/03_Assets")
    ap.add_argument("--commit", action="store_true",
                    help="apply changes (default: dry-run)")
    args = ap.parse_args(argv)

    if not os.path.exists(args.site):
        sys.exit(f"Mock site not found: {args.site} (run: relay_sync.py init --seed)")
    if args.commit and unreal is None:
        print("ERROR: --commit requires the Unreal editor Python environment",
              file=sys.stderr)
        return 2

    # >>> the ONE line that changes for a real ShotGrid site <<<
    sg = MockShotgun(site_file=args.site)

    mode = "COMMIT" if args.commit else "DRY-RUN"
    print(f"=== Relay sync — {sg.base_url} — {args.direction} — {mode} ===")

    if args.direction in ("pull", "both"):
        plan = plan_pull(sg, args.shots_root)
        for e in plan:
            e.setdefault("entity", "shot")
            e["direction"] = "PULL"
        _print_plan(plan)
        if args.commit and execute_pull(sg, plan, args.shots_root, args.ledger):
            return 1

    if args.direction in ("push", "both"):
        if unreal is None:
            print("\nPUSH  (skipped outside the Unreal editor — needs the content browser)")
            if not args.commit:
                print("       run `py ue_relay.py --direction push --commit` in-editor")
        else:
            plan = plan_push(sg, args.assets_root)
            for e in plan:
                e["entity"] = "asset"
                e["direction"] = "PUSH"
            _print_plan(plan)
            if args.commit and execute_push(sg, plan, args.ledger):
                return 1

    if not args.commit:
        print("\nDry-run — add --commit to apply. SG mutations land in EventLogEntry,")
        print("engine actions append to", args.ledger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
