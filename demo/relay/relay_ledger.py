"""
Relay sync ledger — local, append-only audit of what the sync actually did.

ShotGrid itself records tracker mutations as EventLogEntry rows; this ledger
covers the engine side (LevelSequences created/updated on pull, etc.) and the
result of every push attempt. Plain JSON lines, one object per line.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append(path: str, direction: str, entity: str, key: str,
           action: str, detail: str = "") -> dict:
    entry = {"ts": now_iso(), "direction": direction, "entity": entity,
             "key": key, "action": action, "detail": detail}
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def read(path: str, limit: int = 20) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    return rows[-limit:][::-1]
