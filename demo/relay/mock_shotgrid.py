"""
MockShotgun — an in-process, JSON-backed mock of the ShotGrid Python API
============================================================================

An original demo by Wei Zeng. This implements the small slice of shotgun_api3
that a Unreal pipeline integration actually uses:

    sg = MockShotgun("https://demo.shotgunstudio.com", "script_user", "***",
                     site_file="sg_site.json")
    sg.find("Shot",
            [["sg_status_list", "is_not", "omt"]],
            ["code", "sg_sequence", "sg_frame_in", "sg_status_list", "updated_at"],
            order=[{"field_name": "code", "direction": "asc"}])
    sg.find_one("Asset", [["code", "is", "SM_Prop_Chair_01"]])
    sg.create("Asset", {"code": "SM_Prop_Lamp_02", "sg_asset_type": "Prop", ...})
    sg.update("Shot", shot_id, {"sg_status_list": "apr"})

Everything is persisted in a human-readable JSON file instead of a server.
To point the same sync code at a real site, the *only* line that changes is:

    from mock_shotgrid import MockShotgun      # demo
    # from shotgun_api3 import Shotgun         # production

Entity links follow the ShotGrid convention: {"type": "Sequence", "id": 2}.
Dotted field paths are resolved like the real API:
"sg_sequence.Sequence.code". Mutations automatically stamp created_at /
updated_at / updated_by and append an EventLogEntry row — just like ShotGrid
does on the real site.

Differences from the real API (kept simple on purpose): timestamps are ISO
strings instead of timezone-aware datetimes; pagination is omitted.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional


# ShotGrid-style status short codes.
STATUS_LABELS = {
    "ip": "In Progress",
    "wtg": "Waiting to Start",
    "hld": "On Hold",
    "apr": "Approved",
    "fin": "Final",
    "omt": "Omitted",
    "na": "N/A",
}

_SCRIPT_USER = {"type": "ApiUser", "id": 1, "name": "relay_script_user"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MockShotgunError(RuntimeError):
    pass


class MockShotgun:
    """JSON-backed stand-in for shotgun_api3.Shotgun."""

    def __init__(self, base_url: str = "https://demo.shotgunstudio.com",
                 script_name: str = "relay_script",
                 api_key: str = "mock-key",
                 site_file: str = "sg_site.json") -> None:
        self.base_url = base_url.rstrip("/")
        self.script_name = script_name
        self.api_key = api_key
        self.site_file = site_file
        self._store: dict[str, dict[str, dict]] = {}
        self._next_id: dict[str, int] = {}
        self._load()

    # ------------------------------------------------------------------ io #
    def _load(self) -> None:
        if os.path.exists(self.site_file):
            with open(self.site_file, "r", encoding="utf-8") as fh:
                blob = json.load(fh)
            self._store = blob.get("entities", {})
            self._next_id = blob.get("next_id", {})

    def _save(self) -> None:
        tmp = self.site_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"entities": self._store, "next_id": self._next_id},
                      fh, indent=2)
        os.replace(tmp, self.site_file)

    def _rows(self, entity_type: str) -> dict[str, dict]:
        return self._store.setdefault(entity_type, {})

    def _get(self, entity_type: str, entity_id: int) -> dict:
        row = self._rows(entity_type).get(str(entity_id))
        if row is None:
            raise MockShotgunError(f"{entity_type} {entity_id} not found")
        return row

    # ------------------------------------------------------------- queries #
    def find(self, entity_type: str, filters: list[list],
             fields: Optional[list[str]] = None,
             order: Optional[list[dict]] = None,
             filter_operator: str = "all") -> list[dict]:
        results = []
        for row in self._rows(entity_type).values():
            if self._matches(row, entity_type, filters, filter_operator):
                results.append(self._project(row, fields))
        if order:
            for spec in reversed(order):
                field = spec.get("field_name")
                reverse = spec.get("direction", "asc") == "desc"
                results.sort(
                    key=lambda r: ("\uffff" if _sort_key(r, field) is None
                                   else "", _sort_key(r, field)),
                    reverse=reverse)
        return results

    def find_one(self, entity_type: str, filters: list[list],
                 fields: Optional[list[str]] = None,
                 order: Optional[list[dict]] = None) -> Optional[dict]:
        rows = self.find(entity_type, filters, fields, order)
        return rows[0] if rows else None

    # ------------------------------------------------------------ mutations #
    def create(self, entity_type: str, data: dict) -> dict:
        if "code" in data and self.find_one(entity_type, [["code", "is", data["code"]]]):
            raise MockShotgunError(
                f"{entity_type} code already exists: {data['code']}")
        new_id = self._next_id.get(entity_type, 0) + 1
        self._next_id[entity_type] = new_id
        ts = now_iso()
        row = {**data, "id": new_id, "type": entity_type,
               "created_at": ts, "updated_at": ts,
               "created_by": _SCRIPT_USER, "updated_by": _SCRIPT_USER}
        self._rows(entity_type)[str(new_id)] = row
        self._log_event(entity_type, new_id, "create",
                        f"Created {entity_type} {data.get('code', new_id)}", data)
        self._save()
        return dict(row)

    def update(self, entity_type: str, entity_id: int, data: dict) -> dict:
        row = self._get(entity_type, entity_id)
        if "id" in data or "type" in data:
            raise MockShotgunError("id/type are not writable")
        row.update(data)
        row["updated_at"] = now_iso()
        row["updated_by"] = _SCRIPT_USER
        self._log_event(entity_type, entity_id, "update",
                        f"Updated {entity_type} {row.get('code', entity_id)}", data)
        self._save()
        return dict(row)

    def delete(self, entity_type: str, entity_id: int) -> bool:
        if str(entity_id) in self._rows(entity_type):
            del self._rows(entity_type)[str(entity_id)]
            self._log_event(entity_type, entity_id, "delete",
                            f"Deleted {entity_type} {entity_id}", {})
            self._save()
            return True
        return False

    # ------------------------------------------------------- filter engine #
    def _resolve(self, row: dict, entity_type: str, field: str) -> Any:
        """Resolve plain or dotted (linked) fields, SG-style."""
        if "." not in field:
            return row.get(field)
        link_field, rest = field.split(".", 1)
        link = row.get(link_field)
        if not isinstance(link, dict) or "id" not in link:
            return None
        linked_type = link.get("type")
        linked = self._rows(linked_type).get(str(link["id"]))
        if linked is None:
            return None
        # rest looks like "Sequence.code" — strip the type prefix.
        if "." in rest:
            _, sub_field = rest.split(".", 1)
        else:
            sub_field = rest
        return linked.get(sub_field)

    def _matches(self, row: dict, entity_type: str,
                 filters: list[list], mode: str) -> bool:
        checks = [self._check(row, entity_type, f) for f in filters]
        return all(checks) if mode != "any" else any(checks)

    def _check(self, row: dict, entity_type: str, cond: list) -> bool:
        field, relation, wanted = cond[0], cond[1], cond[2]
        value = self._resolve(row, entity_type, field)
        rel = relation.lower().replace("_", " ")
        if rel in ("is", "="):
            return value == wanted
        if rel in ("is not", "!="):
            return value != wanted
        if rel == "in":
            return value in wanted
        if rel == "not in":
            return value not in wanted
        if rel in ("contains", "name contains"):
            return wanted.lower() in str(value or "").lower()
        if rel == "starts with":
            return str(value or "").lower().startswith(str(wanted).lower())
        if rel in ("greater than", ">"):
            return value is not None and value > wanted
        if rel in ("less than", "<"):
            return value is not None and value < wanted
        if rel in ("greater than or equal", ">="):
            return value is not None and value >= wanted
        if rel in ("less than or equal", "<="):
            return value is not None and value <= wanted
        if rel == "between":
            lo, hi = wanted
            return value is not None and lo <= value <= hi
        raise MockShotgunError(f"unsupported filter relation: {relation}")

    def _project(self, row: dict, fields: Optional[list[str]]) -> dict:
        out = {"type": row["type"], "id": row["id"]}
        if not fields:
            return {**out, **{k: v for k, v in row.items()
                              if k not in ("type",)}}
        for f in fields:
            if "." in f:
                out[f] = self._resolve(row, row["type"], f)
            elif f in row:
                out[f] = row[f]
        return out

    # -------------------------------------------------------------- events #
    def _log_event(self, entity_type: str, entity_id: int, operation: str,
                   description: str, changes: dict) -> None:
        table = self._rows("EventLogEntry")
        new_id = self._next_id.get("EventLogEntry", 0) + 1
        self._next_id["EventLogEntry"] = new_id
        table[str(new_id)] = {
            "id": new_id, "type": "EventLogEntry",
            "event_type": f"Shotgun_{entity_type}_{operation}",
            "entity": {"type": entity_type, "id": entity_id},
            "operation": operation,
            "description": description,
            "created_at": now_iso(),
            "user": _SCRIPT_USER,
            "changes": changes,
        }


def _sort_key(item: dict, field: str):
    value = item.get(field)
    if isinstance(value, dict):
        return value.get("id")
    return value


# --------------------------------------------------------------------------- #
#  Fictional demo site
# --------------------------------------------------------------------------- #

def seed_site(sg: MockShotgun) -> int:
    """Populate a small, entirely fictional show. Returns entity count.
    Safe to re-run: does nothing if the site already has entities."""
    if sg.find_one("Project", [["name", "is", "Demo Show"]]):
        return 0

    users = {}
    for name, login in (("Ava Director", "a.director"), ("Wei Cam", "wei.cam")):
        users[login] = sg.create(
            "HumanUser", {"name": name, "login": login, "email": f"{login}@demo.film"})

    project = sg.create("Project", {"name": "Demo Show", "code": "demo_show",
                                    "sg_status_list": "ip"})
    seq_ids = {}
    for code, name, status in (("SQ010", "The Approach", "ip"),
                               ("SQ020", "The Reveal", "ip"),
                               ("SQ900", "Finale", "omt")):
        seq_ids[code] = sg.create("Sequence", {
            "code": code, "content": name, "sg_status_list": status,
            "project": project_link(project),
        })

    # Shot codes are unique within the project, SG-style.
    shots = [
        ("SQ010", "SH010", 1001, 1085, "apr", "a.director"),
        ("SQ010", "SH020", 1086, 1210, "ip",  "wei.cam"),
        ("SQ010", "SH030", 1211, 1300, "ip",  "wei.cam"),
        ("SQ020", "SH040", 2001, 2120, "hld", None),
        ("SQ900", "SH900", 9001, 9100, "omt", None),
    ]
    for seq_code, code, fi, fo, status, assignee in shots:
        sg.create("Shot", {
            "code": code,
            "project": project_link(project),
            "sg_sequence": {"type": "Sequence", "id": seq_ids[seq_code]["id"]},
            "sg_frame_in": fi, "sg_frame_out": fo,
            "sg_status_list": status,
            "task_assignees": [{"type": "HumanUser", "id": users[assignee]["id"]}]
                              if assignee else [],
        })

    assets = [
        ("SM_Prop_Chair_01", "Prop", "/Game/03_Assets/Props", 3, 1840),
        ("SK_Char_Hero", "Character", "/Game/03_Assets/Characters", 1, 12840),
    ]
    for code, atype, path, lods, tris in assets:
        sg.create("Asset", {
            "code": code,
            "project": project_link(project),
            "sg_asset_type": atype,
            "sg_package_path": path,
            "sg_lod_count": lods,
            "sg_tri_count": tris,
            "sg_status_list": "ip",
        })

    return len(shots) + len(assets) + 3 + len(users) + 1


def project_link(project: dict) -> dict:
    return {"type": "Project", "id": project["id"]}
