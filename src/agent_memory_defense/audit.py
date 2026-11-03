"""Hash-chained audit log.

Every memory mutation appends one record whose hash chains to the
previous record. Any later edit, deletion, or reordering breaks the
chain, which :func:`AuditLog.verify` detects.
"""
from __future__ import annotations

import hashlib
import json


def _digest(prev_hash: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{prev_hash}|{canonical}".encode("utf-8")).hexdigest()


class AuditLog:
    """Append-only, hash-chained audit trail."""

    def __init__(self) -> None:
        self.records: list[dict] = []
        self._prev_hash = "GENESIS"

    def append(self, action: str, entry_id: str, actor: str, detail: str = "") -> dict:
        payload = {
            "index": len(self.records),
            "action": action,
            "entry_id": entry_id,
            "actor": actor,
            "detail": detail,
        }
        record = dict(payload)
        record["prev_hash"] = self._prev_hash
        record["hash"] = _digest(self._prev_hash, payload)
        self.records.append(record)
        self._prev_hash = record["hash"]
        return record

    def verify(self) -> bool:
        """Return True only if the whole chain recomputes cleanly."""
        prev = "GENESIS"
        for i, record in enumerate(self.records):
            payload = {
                "index": i,
                "action": record["action"],
                "entry_id": record["entry_id"],
                "actor": record["actor"],
                "detail": record["detail"],
            }
            if record["prev_hash"] != prev:
                return False
            if record["hash"] != _digest(prev, payload):
                return False
            prev = record["hash"]
        return True

    def actions_for(self, entry_id: str) -> list[str]:
        return [r["action"] for r in self.records if r["entry_id"] == entry_id]
