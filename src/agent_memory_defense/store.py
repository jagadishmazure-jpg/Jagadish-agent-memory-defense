"""The memory store: entries, snapshots, quarantine, and audit.

Every mutation appends to the hash-chained audit log. Snapshots are
deep copies of active entries so rollback restores a prior good state.
"""
from __future__ import annotations

import copy

from .audit import AuditLog
from .models import MemoryEntry, Snapshot
from .redaction import redact


class MemoryStore:
    def __init__(self) -> None:
        self.entries: dict[str, MemoryEntry] = {}
        self.snapshots: dict[str, Snapshot] = {}
        self.audit = AuditLog()
        self.step = 0

    def tick(self) -> int:
        self.step += 1
        return self.step

    def add(self, entry: MemoryEntry, actor: str = "system") -> MemoryEntry:
        self.entries[entry.entry_id] = entry
        self.audit.append("add", entry.entry_id, actor, redact(entry.content[:80]))
        return entry

    def update(self, entry_id: str, content: str, actor: str = "system",
               approved_change: bool = False) -> MemoryEntry:
        entry = self.entries[entry_id]
        entry.content = content
        entry.updated_step = self.step
        entry.approved_change = approved_change
        self.audit.append("update", entry_id, actor, redact(content[:80]))
        return entry

    def snapshot(self, snapshot_id: str) -> Snapshot:
        snap = Snapshot(
            snapshot_id=snapshot_id,
            step=self.step,
            entries=copy.deepcopy(
                {k: v for k, v in self.entries.items() if not v.quarantined}
            ),
        )
        self.snapshots[snapshot_id] = snap
        self.audit.append("snapshot", snapshot_id, "system", f"{len(snap.entries)} entries")
        return snap

    def restore(self, snapshot_id: str, actor: str) -> list[str]:
        """Restore active entries from a snapshot; returns restored ids."""
        snap = self.snapshots[snapshot_id]
        restored = []
        for entry_id, saved in snap.entries.items():
            self.entries[entry_id] = copy.deepcopy(saved)
            restored.append(entry_id)
        # Entries created after the snapshot and not in it stay quarantined
        # or are left untouched; rollback never silently deletes audit history.
        self.audit.append("rollback", snapshot_id, actor, f"{len(restored)} entries restored")
        return restored

    def active_entries(self) -> list[MemoryEntry]:
        return [e for e in self.entries.values() if not e.quarantined]

    def quarantined_entries(self) -> list[MemoryEntry]:
        return [e for e in self.entries.values() if e.quarantined]
