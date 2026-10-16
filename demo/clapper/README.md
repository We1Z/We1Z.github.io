# Clapper — Unreal Asset & Shot Importer (Demo)

An original demo tool by Wei Zeng. This is how I actually work: Python inside
Unreal, driven by a manifest, safe by default.

## What it does

- Reads one JSON manifest describing assets and shots
- Builds sequence/shot folder structure and creates a **LevelSequence per shot**
- Imports FBX/texture sources through Unreal's real `AssetTools` pipeline
- **Auto-conforms names** to the show's prefix convention (`Prop_Chair_01` → `SM_Prop_Chair_01`)
- Tags assets/sequences with metadata (sequence, shot, frame range, source file)
- **Dry-run by default** — `--commit` is required to touch the project
- Writes a machine-readable JSON report
- Manifest validation runs in plain Python 3, so it can gate CI without an editor

## Run it

Inside the Unreal editor (Output Log → Cmd; enable the Python Editor Script Plugin):

```
py clapper_importer.py --manifest import_manifest.example.json
py clapper_importer.py --manifest import_manifest.example.json --commit
```

Outside Unreal (pre-flight / CI):

```bash
python3 clapper_importer.py --manifest import_manifest.example.json --validate-only
python3 clapper_importer.py --manifest import_manifest.example.json --report report.json
```

The example manifest uses fictional paths and names; on a machine without those
source files the importer dry-runs the full folder/sequence/rename plan and marks
the file imports as SKIP — nothing errors out.

## Why it exists

Production import code is confidential. Clapper was written independently to
demonstrate the same patterns: manifest-driven ingest, naming enforcement, shot
structure, metadata tagging, dry-run safety and structured reporting.
