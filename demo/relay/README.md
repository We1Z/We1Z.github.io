# Relay — Unreal ⇄ ShotGrid Sync (Demo)

An original demo by Wei Zeng. Bidirectional sync between Unreal and a
production tracker, built against a **mocked ShotGrid site** — no SQL, no
server, no credentials. The mock implements the slice of `shotgun_api3` a
pipeline actually uses (`find` / `find_one` / `create` / `update`, entity
links, dotted fields, `EventLogEntry`), so the sync code is written exactly
the way it would be against your real site.

```
mock_shotgrid.py   JSON-backed mock of shotgun_api3.Shotgun
                   find / find_one / create / update + EventLogEntry
sg_site.json       fictional seeded site — a project, sequences, shots,
                   assets, users — open it in any text editor
relay_sync.py      coordinator CLI (what a producer / CI would run)
ue_relay.py        the Unreal-side bidirectional sync
relay_ledger.py    append-only local log of engine-side sync actions
```

## Going to a real ShotGrid site — one line

`ue_relay.py` talks to the tracker through one object:

```python
sg = MockShotgun(site_file="sg_site.json")        # demo
# sg = shotgun_api3.Shotgun(base_url,             # production
#                           script_name=..., api_key=...)
```

Every call after that — `sg.find("Shot", filters, fields)`, `sg.create(...)`,
`sg.update(...)` — is identical on both sides.

## Try it — coordinator side (plain Python 3, no installs)

```bash
python3 relay_sync.py init --seed          # seeds sg_site.json
python3 relay_sync.py shots                # SG shots, omitted hidden
python3 relay_sync.py assets
python3 relay_sync.py set-shot SQ010 SH020 apr   # producer approves a shot
python3 relay_sync.py events               # ShotGrid EventLogEntry feed
python3 relay_sync.py log                  # local sync ledger
```

Status codes are the real ShotGrid short codes: `ip` (In Progress), `wtg`,
`hld` (On Hold), `apr` (Approved), `fin`, `omt`.

## Try it — engine side

The PULL plan runs anywhere with just Python:

```bash
python3 ue_relay.py --direction pull
```

Inside the Unreal editor (Python Editor Script Plugin enabled):

```
py ue_relay.py --direction both --commit
```

## What each direction does

**PULL (ShotGrid → Unreal).** `sg.find("Shot", …)` returns every shot that
isn't omitted; each becomes
`/Game/Cinematics/Sequences/SQ/SH/LS_SQ_SH` with metadata tags for frames,
SG status, assignees and an `sg_updated_at` stamp. On the next sync the stamp
is compared with ShotGrid's `updated_at`: equal → SKIP, ShotGrid newer →
UPDATE, engine stamped ahead → CONFLICT (ShotGrid wins, logged).

**PUSH (Unreal → ShotGrid).** Scans `/Game/03_Assets` for Static and
Skeletal Meshes, then `find_one("Asset", [["code","is", code]])` decides
between `create` and `update` (asset type, package path, LOD count). Unchanged
assets SKIP, so re-runs are idempotent.

Tracker mutations automatically appear as **EventLogEntry** rows — the same
audit feed a real ShotGrid site writes — and engine-side actions append to
the local JSON-lines ledger. Everything is dry-run by default; `--commit`
applies.

## Why it exists

Real ShotGrid integration (credentials, projects, show data) is
confidential. Relay independently demonstrates the transferable skills: the
ShotGrid entity API and filter syntax, entity-link conventions,
timestamp-based change/conflict detection, idempotent two-way sync, and
metadata-tag interchange with Unreal assets.
