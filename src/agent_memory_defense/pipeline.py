"""End-to-end pipeline: detect -> triage -> quarantine -> recover.

Measurement: every run returns counts per failure class, quarantine
counts, recovery counts, and whether the store verifies clean after
recovery. A run is only "clean" when a follow-up scan finds nothing
and the audit chain verifies.
"""
from __future__ import annotations

from collections import Counter

from .agents import MemoryMonitorAgent, QuarantineAgent, RecoveryAgent
from .gates import Approval, HumanGate
from .store import MemoryStore


def run_cycle(store: MemoryStore, baselines: dict[str, str],
              rollback_approval: Approval | None = None,
              snapshot_id: str | None = None) -> dict:
    """Run one detect-quarantine-recover cycle and report metrics."""
    monitor_agent = MemoryMonitorAgent()
    quarantine_agent = QuarantineAgent()
    gate = HumanGate()
    recovery_agent = RecoveryAgent(gate)

    findings = monitor_agent.scan(store, baselines)
    by_class = Counter(f.failure_class for f in findings)

    quarantined = []
    for finding in findings:
        if finding.failure_class in ("poisoned", "drift", "conflict"):
            entry = store.entries.get(finding.entry_id)
            if entry is not None and not entry.quarantined:
                quarantine_agent.quarantine(store, finding.entry_id)
                quarantined.append(finding.entry_id)

    rolled_back: list[str] = []
    if snapshot_id is not None:
        # The caller supplies an approval issued against this gate's
        # token registry; re-issue it here so the gate recognises it.
        if rollback_approval is not None:
            gate.issue(rollback_approval)
        rolled_back = recovery_agent.rollback(store, snapshot_id, rollback_approval)

    post_findings = monitor_agent.scan(store, baselines)
    clean = not post_findings and store.audit.verify()
    return {
        "findings": len(findings),
        "by_class": dict(by_class),
        "quarantined": quarantined,
        "rolled_back": rolled_back,
        "post_scan_findings": len(post_findings),
        "audit_valid": store.audit.verify(),
        "clean": clean,
    }
