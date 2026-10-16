#!/usr/bin/env python3
"""
Relay — coordinator-side CLI for the mock ShotGrid site (demo)
==============================================================

An original demo by Wei Zeng. Talks to MockShotgun with the same calls a real
pipeline uses against shotgun_api3 — no SQL anywhere.

    python3 relay_sync.py init --seed
    python3 relay_sync.py shots
    python3 relay_sync.py assets
    python3 relay_sync.py set-shot SQ010 SH020 apr      # producer approves
    python3 relay_sync.py events                         # ShotGrid EventLogEntry
    python3 relay_sync.py log                            # local sync ledger

Status codes are real ShotGrid short codes: ip · wtg · hld · apr · fin · omt.
Run `ue_relay.py pull` after set-shot to see the change flow into Unreal.
"""

from __future__ import annotations

import argparse

from mock_shotgrid import MockShotgun, STATUS_LABELS, seed_site
import relay_ledger


SHOT_FIELDS = [
    "code", "sg_status_list", "sg_frame_in", "sg_frame_out", "updated_at",
    "sg_sequence.Sequence.code", "task_assignees",
]
ASSET_FIELDS = [
    "code", "sg_asset_type", "sg_package_path", "sg_lod_count",
    "sg_tri_count", "sg_status_list", "updated_at",
]


def connect(path: str) -> MockShotgun:
    return MockShotgun(site_file=path)


def user_names(sg: MockShotgun) -> dict:
    users = sg.find("HumanUser", [], ["name", "login"])
    return {u["id"]: u.get("name", u.get("login", u["id"])) for u in users}


def status(code: str) -> str:
    label = STATUS_LABELS.get(code, code)
    return f"{code} ({label})"


def cmd_init(a: argparse.Namespace) -> int:
    sg = connect(a.site)
    if a.seed:
        n = seed_site(sg)
        print(f"Seeded {a.site}" + (f" — {n} entities created" if n
                                    else " (Demo Show already present)"))
    else:
        print(f"Site file ready: {a.site}")
    return 0


def cmd_shots(a: argparse.Namespace) -> int:
    sg = connect(a.site)
    names = user_names(sg)
    filters = []
    if not a.all:
        filters.append(["sg_status_list", "is_not", "omt"])
        filters.append(["sg_sequence.Sequence.sg_status_list", "is_not", "omt"])
    if a.status:
        filters.append(["sg_status_list", "is", a.status])
    rows = sg.find("Shot", filters, SHOT_FIELDS,
                   order=[{"field_name": "sg_sequence.Sequence.code", "direction": "asc"},
                          {"field_name": "code", "direction": "asc"}])
    print(f"{'SEQ':6} {'SHOT':8} {'FRAMES':12} {'STATUS':18} ASSIGNEE")
    print("-" * 70)
    for r in rows:
        assignees = ", ".join(names.get(u["id"], str(u["id"]))
                              for u in r.get("task_assignees", [])) or "—"
        frames = f'{r.get("sg_frame_in", "")}-{r.get("sg_frame_out", "")}'
        seq = r.get("sg_sequence.Sequence.code") or "?"
        print(f"{seq:6} {r['code']:8} {frames:12} {status(r.get('sg_status_list','')):18} "
              f"{assignees}")
    print(f"\n{len(rows)} shot(s)")
    return 0


def cmd_assets(a: argparse.Namespace) -> int:
    sg = connect(a.site)
    filters = []
    if a.status:
        filters.append(["sg_status_list", "is", a.status])
    rows = sg.find("Asset", filters, ASSET_FIELDS,
                   order=[{"field_name": "code", "direction": "asc"}])
    print(f"{'CODE':20} {'TYPE':10} {'LODS':5} {'TRIS':8} STATUS")
    print("-" * 66)
    for r in rows:
        print(f"{r['code']:20} {r.get('sg_asset_type',''):10} "
              f"{r.get('sg_lod_count', 0):<5} {r.get('sg_tri_count', 0):<8} "
              f"{status(r.get('sg_status_list', ''))}")
    print(f"\n{len(rows)} asset(s)")
    return 0


def cmd_set_shot(a: argparse.Namespace) -> int:
    sg = connect(a.site)
    shot = sg.find_one(
        "Shot",
        [["sg_sequence.Sequence.code", "is", a.sequence], ["code", "is", a.shot]],
        ["code", "sg_status_list"])
    if shot is None:
        print(f"No shot {a.sequence}/{a.shot}", flush=True)
        return 1
    sg.update("Shot", shot["id"], {"sg_status_list": a.status})
    relay_ledger.append(a.ledger, "tracker", "shot",
                        f"{a.sequence}/{a.shot}", "update",
                        f"sg_status_list → {a.status}")
    print(f"{a.sequence}/{a.shot} → {a.status}  "
          f"(pending pull on next UE sync)")
    return 0


def cmd_events(a: argparse.Namespace) -> int:
    sg = connect(a.site)
    rows = sg.find("EventLogEntry", [],
                   ["event_type", "entity", "description", "created_at"],
                   order=[{"field_name": "id", "direction": "desc"}])
    for r in rows[:a.limit]:
        ent = r.get("entity") or {}
        print(f'{r["created_at"]}  {r["event_type"]:28} '
              f'{ent.get("type","?")} {ent.get("id","?"):>4}  {r.get("description","")}')
    print(f"\n{min(len(rows), a.limit)} event(s)")
    return 0


def cmd_log(a: argparse.Namespace) -> int:
    rows = relay_ledger.read(a.ledger, limit=a.limit)
    if not rows:
        print("(local sync ledger is empty — run a sync --commit first)")
        return 0
    for r in rows:
        print(f'{r["ts"]}  {r["direction"]:8} {r["entity"]:5} '
              f'{r["key"]:24} {r["action"]:9} {r["detail"]}')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Relay — mock ShotGrid CLI (demo)")
    ap.add_argument("--site", default="sg_site.json")
    ap.add_argument("--ledger", default="relay_sync_log.jsonl")
    sub = ap.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create + seed the mock site")
    p_init.add_argument("--seed", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_shots = sub.add_parser("shots", help="list shots (omitted hidden)")
    p_shots.add_argument("--status", help="filter by SG code, e.g. ip / apr / hld")
    p_shots.add_argument("--all", action="store_true")
    p_shots.set_defaults(func=cmd_shots)

    p_assets = sub.add_parser("assets")
    p_assets.add_argument("--status")
    p_assets.set_defaults(func=cmd_assets)

    p_set = sub.add_parser("set-shot", help="producer changes a shot's SG status")
    p_set.add_argument("sequence")
    p_set.add_argument("shot")
    p_set.add_argument("status", choices=["ip", "wtg", "hld", "apr", "fin", "omt"])
    p_set.set_defaults(func=cmd_set_shot)

    p_events = sub.add_parser("events", help="ShotGrid EventLogEntry feed")
    p_events.add_argument("--limit", type=int, default=15)
    p_events.set_defaults(func=cmd_events)

    p_log = sub.add_parser("log", help="local sync ledger")
    p_log.add_argument("--limit", type=int, default=20)
    p_log.set_defaults(func=cmd_log)

    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
