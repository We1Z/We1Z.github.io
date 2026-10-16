"""
Clapper — Asset & Shot Importer for Unreal Engine (demo tool)
==============================================================

An original, portfolio-grade demo by Wei Zeng. Mirrors the kind of show-floor
tooling I build at the studio:

  * manifest-driven ingest (one JSON file describes every asset and shot)
  * naming-convention validation with optional auto-fix
  * shot / sequence folder structure built from the manifest
  * one LevelSequence per shot, tagged with sequence/shot/frame metadata
  * FBX / texture import through the real AssetTools import pipeline
  * dry-run by default — nothing changes in the project until --commit
  * machine-readable JSON report

This file intentionally contains NO studio code, paths, show names or data.

------------------------------------------------------------------------------
RUN INSIDE UNREAL EDITOR (Python must be enabled in plugins)
------------------------------------------------------------------------------
  Output Log > Cmd:

      py clapper_importer.py --manifest import_manifest.example.json
      py clapper_importer.py --manifest import_manifest.example.json --commit

  Drop both files in <Project>/Saved/Python/ (or any folder on the UE
  python path) and use absolute paths for --manifest.

------------------------------------------------------------------------------
RUN THE VALIDATOR OUTSIDE UNREAL (dry validation / CI, no editor needed)
------------------------------------------------------------------------------
  Any plain Python 3 can parse and validate manifests:

      python clapper_importer.py --manifest import_manifest.example.json --validate-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

# `unreal` only exists inside the editor's Python environment.
try:
    import unreal
except ImportError:  # allow manifest validation from plain Python / CI
    unreal = None


# --------------------------------------------------------------------------- #
#  Data model
# --------------------------------------------------------------------------- #

@dataclass
class Step:
    """One planned (or executed) action."""
    action: str                 # import | mkdir | rename | sequence | tag
    target: str                 # package path or asset name
    detail: str = ""
    status: str = "PLANNED"     # PLANNED | DONE | FIXED | SKIP | ERROR
    note: str = ""


@dataclass
class Report:
    tool: str = "Clapper"
    committed: bool = False
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    steps: list[Step] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add(self, step: Step) -> None:
        self.steps.append(step)
        line = f"[{step.status:7}] {step.action:8} {step.target}"
        if step.detail:
            line += f"  ({step.detail})"
        unreal.log(line) if unreal else print(line)

    def fail(self, message: str) -> None:
        self.errors.append(message)
        (unreal.log_error if unreal else print)(message)

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for s in self.steps:
            counts[s.status] = counts.get(s.status, 0) + 1
        return {"total": len(self.steps), "errors": len(self.errors), **counts}

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "committed": self.committed,
            "started_at": self.started_at,
            "summary": self.summary(),
            "errors": self.errors,
            "steps": [asdict(s) for s in self.steps],
        }


# --------------------------------------------------------------------------- #
#  Core importer
# --------------------------------------------------------------------------- #

def conform_name(name: str, expected_prefix: str, known_prefixes: set[str]) -> tuple[str, bool]:
    """Apply the expected prefix. A different *known* prefix is replaced;
    an arbitrary leading token is kept (treated as a missing prefix)."""
    prefix = name.split("_", 1)[0] if "_" in name else ""
    if prefix == expected_prefix:
        return name, False
    stem = name.split("_", 1)[1] if prefix in known_prefixes and "_" in name else name
    return f"{expected_prefix}_{stem}", True


class ClapperImporter:
    """
    Manifest format (see import_manifest.example.json):

      content_root / assets_root / shots_root : virtual UE package roots
      naming : { "Static Mesh": "SM", ... }  expected name prefixes per class
      assets : [{ source, type, category, name, shot }]
      shots  : [{ sequence, shot, frame_in, frame_out, create_sequence }]
    """

    def __init__(self, manifest: dict[str, Any], commit: bool = False):
        self.m = manifest
        self.commit = commit and unreal is not None
        self.report = Report(committed=commit and unreal is not None)
        self.eal = unreal.EditorAssetLibrary if unreal else None
        self.asset_tools = unreal.AssetToolsHelpers.get_asset_tools() if unreal else None

        if commit and unreal is None:
            self.report.fail("--commit requested but unreal module is unavailable; running dry")

    # -- public entry point ------------------------------------------------- #

    def run(self) -> Report:
        self._build_shot_structure()
        self._process_assets()
        self.report.add(Step(
            action="report",
            target="manifest ingest",
            detail=f"{self.report.summary()}",
            status="DONE",
        ))
        return self.report

    # -- helpers ------------------------------------------------------------ #

    @staticmethod
    def _norm(path: str) -> str:
        return path.replace("\\", "/").rstrip("/")

    def _ensure_folder(self, package_dir: str) -> None:
        package_dir = self._norm(package_dir)
        if not self.commit:
            self.report.add(Step("mkdir", package_dir, status="PLANNED",
                                 note="dry-run — folder would be created"))
            return
        if not self.eal.does_directory_exist(package_dir):
            self.eal.make_directory(package_dir)
        self.report.add(Step("mkdir", package_dir, status="DONE"))

    def _shot_dir(self, sequence: str, shot: str) -> str:
        root = self._norm(self.m.get("shots_root", "/Game/Cinematics/Sequences"))
        return f"{root}/{sequence}/{shot}"

    def _asset_dir(self, entry: dict[str, Any]) -> str:
        root = self._norm(self.m.get("assets_root", "/Game/Assets"))
        return f"{root}/{entry['category'].strip('/')}"

    # -- shots -------------------------------------------------------------- #

    def _build_shot_structure(self) -> None:
        seen: set[str] = set()
        for shot in self.m.get("shots", []):
            seq, code = shot.get("sequence"), shot.get("shot")
            if not seq or not code:
                self.report.fail(f"shot entry missing sequence/shot: {shot}")
                continue

            seq_dir = self._norm(
                f"{self.m.get('shots_root', '/Game/Cinematics/Sequences')}/{seq}")
            shot_dir = self._shot_dir(seq, code)
            for d in (seq_dir, shot_dir):
                if d in seen:
                    continue
                seen.add(d)
                self._ensure_folder(d)

            if shot.get("create_sequence"):
                self._create_level_sequence(shot, shot_dir)

    def _create_level_sequence(self, shot: dict[str, Any], shot_dir: str) -> None:
        target = f"{shot_dir}/LS_{shot['sequence']}_{shot['shot']}"
        if not self.commit:
            self.report.add(Step("sequence", target,
                                 detail=f"frames {shot['frame_in']}-{shot['frame_out']}",
                                 status="PLANNED", note="dry-run"))
            return

        if self.eal.does_asset_exist(target):
            self.report.add(Step("sequence", target, status="SKIP", note="already exists"))
            return

        factory = unreal.LevelSequenceFactoryNew()
        asset = self.asset_tools.create_asset(
            f"LS_{shot['sequence']}_{shot['shot']}",
            shot_dir, unreal.LevelSequence, factory)
        if asset is None:
            self.report.fail(f"failed to create LevelSequence at {target}")
            return

        self._tag(asset, {
            "sequence": shot["sequence"],
            "shot": shot["shot"],
            "frame_in": str(shot["frame_in"]),
            "frame_out": str(shot["frame_out"]),
            "ingest_tool": "Clapper",
        })
        self.report.add(Step("sequence", target,
                             detail=f"frames {shot['frame_in']}-{shot['frame_out']}",
                             status="DONE"))

    # -- assets ------------------------------------------------------------- #

    def _process_assets(self) -> None:
        for entry in self.m.get("assets", []):
            errors = self._validate_entry(entry)
            if errors:
                for e in errors:
                    self.report.fail(e)
                self.report.add(Step("import", entry.get("source", "?"),
                                     status="ERROR", note="; ".join(errors)))
                continue

            fixed_name, renamed = self._conforming_name(entry)
            dest_dir = self._asset_dir(entry)
            dest_path = f"{dest_dir}/{fixed_name}"
            self._ensure_folder(dest_dir)

            if entry.get("shot"):
                self._ensure_folder(self._shot_dir(
                    next((s["sequence"] for s in self.m["shots"]
                          if s["shot"] == entry["shot"]), "SQ000"),
                    entry["shot"]))

            self._import_file(entry, dest_dir, fixed_name, dest_path, renamed)

    def _validate_entry(self, entry: dict[str, Any]) -> list[str]:
        problems = []
        for key in ("source", "type", "category", "name"):
            if not entry.get(key):
                problems.append(f"asset entry missing '{key}'")
        if entry.get("type") not in self.m.get("naming", {}):
            problems.append(f"unknown asset type '{entry.get('type')}' — add it to naming map")
        return problems

    def _conforming_name(self, entry: dict[str, Any]) -> tuple[str, bool]:
        """Return (name, was_fixed). Auto-fixes wrong/empty prefix."""
        fixed, changed = conform_name(
            entry["name"], self.m["naming"][entry["type"]], set(self.m["naming"].values()))
        if changed:
            self.report.add(Step("rename", entry["name"], detail=f"→ {fixed}",
                                 status="FIXED" if self.commit else "PLANNED"))
        return fixed, changed

    def _import_file(self, entry: dict[str, Any], dest_dir: str,
                     fixed_name: str, dest_path: str, renamed: bool) -> None:
        source = entry["source"]
        if not os.path.isfile(source):
            self.report.add(Step("import", source, detail=f"→ {dest_path}",
                                 status="SKIP",
                                 note="source file not found on this machine — demo paths are fictional"))
            return

        if not self.commit:
            self.report.add(Step("import", source, detail=f"→ {dest_path}",
                                 status="PLANNED", note="dry-run"))
            return

        if self.eal.does_asset_exist(dest_path):
            self.report.add(Step("import", dest_path, status="SKIP", note="asset already exists"))
            return

        task = unreal.AssetImportTask()
        task.set_editor_property("filename", source)
        task.set_editor_property("destination_path", dest_dir)
        task.set_editor_property("destination_name", fixed_name)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("replace_existing", True)
        self.asset_tools.import_asset_tasks([task])

        asset = self.eal.load_asset(dest_path)
        if asset is None:
            self.report.fail(f"import reported success but asset missing: {dest_path}")
            return

        tags = {"ingest_tool": "Clapper", "source_file": os.path.basename(source)}
        if entry.get("shot"):
            tags["shot"] = entry["shot"]
        self._tag(asset, tags)
        self.report.add(Step("import", source, detail=f"→ {dest_path}",
                             status="FIXED" if renamed else "DONE"))

    # -- metadata ----------------------------------------------------------- #

    def _tag(self, asset: Any, tags: dict[str, str]) -> None:
        """Set editor metadata tags, with a fallback across API versions."""
        for key, value in tags.items():
            try:
                if hasattr(self.eal, "set_metadata_tag"):
                    self.eal.set_metadata_tag(asset, key, value)
                else:  # older API spelling
                    asset.set_metadata_tag(unreal.Name(key), value)
            except Exception as exc:  # metadata must never break ingest
                self.report.fail(f"metadata tag '{key}' failed: {exc}")


# --------------------------------------------------------------------------- #
#  Manifest-only validation (runs without Unreal — handy for CI / pre-flight)
# --------------------------------------------------------------------------- #

def validate_manifest(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (hard_errors, auto_fixable_warnings). Wrong prefixes are warnings
    because the importer conforms them automatically at ingest time."""
    errors: list[str] = []
    warnings: list[str] = []
    naming = manifest.get("naming", {})
    names_seen: set[str] = set()

    for i, entry in enumerate(manifest.get("assets", [])):
        for key in ("source", "type", "category", "name"):
            if not entry.get(key):
                errors.append(f"assets[{i}] missing '{key}'")
        if entry.get("type") not in naming:
            errors.append(f"assets[{i}] type '{entry.get('type')}' not in naming map")
        elif not entry["name"].startswith(naming[entry["type"]] + "_"):
            conformed, _ = conform_name(entry["name"], naming[entry["type"]], set(naming.values()))
            warnings.append(
                f"assets[{i}] '{entry['name']}' will be conformed to '{conformed}' at import")
        if entry.get("name") in names_seen:
            errors.append(f"assets[{i}] duplicate asset name '{entry['name']}'")
        names_seen.add(entry.get("name", ""))

    shots = {(s.get("sequence"), s.get("shot")) for s in manifest.get("shots", [])}
    for i, entry in enumerate(manifest.get("assets", [])):
        if entry.get("shot") and not any(code == entry["shot"] for _, code in shots):
            errors.append(f"assets[{i}] references undeclared shot '{entry['shot']}'")

    for i, shot in enumerate(manifest.get("shots", [])):
        if not shot.get("sequence") or not shot.get("shot"):
            errors.append(f"shots[{i}] needs sequence and shot")
        if int(shot.get("frame_out", 0)) <= int(shot.get("frame_in", 0)):
            errors.append(f"shots[{i}] frame_out must be greater than frame_in")
    return errors, warnings


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Clapper — Unreal asset & shot importer (demo)")
    parser.add_argument("--manifest", required=True, help="path to ingest manifest JSON")
    parser.add_argument("--commit", action="store_true",
                        help="actually create folders/import (default: dry-run)")
    parser.add_argument("--validate-only", action="store_true",
                        help="validate the manifest without the editor (CI/pre-flight)")
    parser.add_argument("--report", help="optional path to write the JSON report")
    args = parser.parse_args(argv)

    try:
        with open(args.manifest, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read manifest: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_manifest(manifest)
    for w in warnings:
        print(f"  ! {w}")
    if errors:
        print("Manifest validation failed:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"Manifest OK — {len(manifest.get('assets', []))} assets, "
          f"{len(manifest.get('shots', []))} shots"
          f" ({len(warnings)} name(s) will be auto-conformed)")

    if args.validate_only:
        return 0

    importer = ClapperImporter(manifest, commit=args.commit)
    mode = "COMMIT" if importer.commit else "DRY-RUN"
    (unreal.log if unreal else print)(f"=== Clapper ingest — {mode} ===")
    report = importer.run()
    print("Summary:", report.summary())

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2)
        print(f"Report written → {args.report}")

    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
