"""The three agents: monitor, quarantine, recovery.

Prevent / detect / respond / recover, with governance (audit + human
gate) and measurement (pipeline metrics) around them.
"""
from __future__ import annotations

from . import monitor
from .gates import Approval, HumanGate
from .models import Finding, MemoryEntry, Retrieval
from .store import MemoryStore


class MemoryMonitorAgent:
    """Detects every class in the failure taxonomy."""

    def __init__(self, ttl_steps: int = 10) -> None:
        self.ttl_steps = ttl_steps

    def scan(self, store: MemoryStore, baselines: dict[str, str],
             retrievals: list[Retrieval] | None = None,
             latest_source_versions: dict[str, int] | None = None) -> list[Finding]:
        findings: list[Finding] = []
        latest_source_versions = latest_source_versions or {}
        for entry in store.entries.values():
            if entry.quarantined:
                continue
            for detector in (
                monitor.detect_poisoned(entry),
                monitor.detect_drift(entry, baselines.get(entry.entry_id)),
                monitor.detect_stuffing(entry),
                monitor.detect_staleness(
                    entry, store.step, self.ttl_steps,
                    latest_source_versions.get(entry.source, entry.source_version)),
            ):
                if detector is not None:
                    findings.append(detector)
        findings.extend(monitor.detect_conflicts(list(store.entries.values())))
        known_ids = set(store.entries)
        for retrieval in retrievals or []:
            found = monitor.detect_hallucination(retrieval, known_ids)
            if found is not None:
                findings.append(found)
        return findings


class QuarantineAgent:
    """Isolates suspect entries so they cannot be retrieved."""

    def quarantine(self, store: MemoryStore, entry_id: str, actor: str = "quarantine-agent") -> MemoryEntry:
        entry = store.entries[entry_id]
        entry.quarantined = True
        store.audit.append("quarantine", entry_id, actor, "isolated pending review")
        return entry

    def release(self, store: MemoryStore, entry_id: str, actor: str = "quarantine-agent") -> MemoryEntry:
        entry = store.entries[entry_id]
        entry.quarantined = False
        store.audit.append("release", entry_id, actor, "returned to active memory")
        return entry


class RecoveryAgent:
    """Destructive recovery: purge and rollback, both human-gated."""

    def __init__(self, gate: HumanGate) -> None:
        self.gate = gate

    def purge(self, store: MemoryStore, entry_id: str, approval: Approval | None,
              actor: str = "recovery-agent") -> str:
        self.gate.authorize(approval, f"purge:{entry_id}", store.step)
        del store.entries[entry_id]
        store.audit.append("purge", entry_id, actor, "permanently removed after approval")
        return entry_id

    def rollback(self, store: MemoryStore, snapshot_id: str, approval: Approval | None,
                 actor: str = "recovery-agent") -> list[str]:
        self.gate.authorize(approval, f"rollback:{snapshot_id}", store.step)
        return store.restore(snapshot_id, actor)

    def reground(self, store: MemoryStore, entry_id: str, source_text: str,
                 actor: str = "recovery-agent") -> MemoryEntry:
        """Non-destructive recovery: replace content from a trusted source."""
        entry = store.entries[entry_id]
        entry.content = source_text
        entry.trust = "trusted"
        entry.quarantined = False
        entry.updated_step = store.step
        store.audit.append("reground", entry_id, actor, "content restored from source")
        return entry
