"""Agent and human-gate tests, including every denied path."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_memory_defense import (
    Approval, GateDenied, HumanGate, MemoryEntry, MemoryStore, parse_consent,
)
from agent_memory_defense.agents import QuarantineAgent, RecoveryAgent


def store_with(entry_id="e-9", content="bad entry"):
    store = MemoryStore()
    store.add(MemoryEntry(entry_id, "k", content, "src", 1, "trusted", 0, 0))
    return store


def gated_recovery():
    gate = HumanGate()
    return gate, RecoveryAgent(gate)


def approval(token="tok-1", scope="purge:e-9", **kw):
    base = dict(approver="Priya Nair", token=token, scope=scope,
                expires_step=10, confidence=1.0, consent_text="yes")
    base.update(kw)
    return Approval(**base)


def test_parse_consent_approved():
    assert parse_consent("Yes, go ahead") == "approved"


def test_parse_consent_rejected():
    assert parse_consent("No") == "rejected"


def test_parse_consent_contradictory():
    assert parse_consent("yes, wait, no") == "contradictory"


def test_parse_consent_unclear():
    assert parse_consent("let me think about it") == "unclear"


def test_quarantine_isolates_entry():
    store = store_with()
    QuarantineAgent().quarantine(store, "e-9")
    assert store.entries["e-9"].quarantined is True
    assert "e-9" not in [e.entry_id for e in store.active_entries()]


def test_release_returns_entry_to_active():
    store = store_with()
    agent = QuarantineAgent()
    agent.quarantine(store, "e-9")
    agent.release(store, "e-9")
    assert store.entries["e-9"].quarantined is False


def test_reground_restores_trusted_content():
    store = store_with()
    QuarantineAgent().quarantine(store, "e-9")
    agent = RecoveryAgent(HumanGate())
    restored = agent.reground(store, "e-9", "Good content from the source handbook.")
    assert restored.content == "Good content from the source handbook."
    assert restored.trust == "trusted" and restored.quarantined is False


def test_rollback_restores_snapshot_content():
    store = MemoryStore()
    store.add(MemoryEntry("e-1", "policy", "Good policy", "src", 1, "trusted", 0, 0))
    store.snapshot("snap-1")
    store.update("e-1", "Tampered policy", actor="ingest")
    gate, agent = gated_recovery()
    ap = approval(token="tok-rb", scope="rollback:snap-1")
    gate.issue(ap)
    restored = agent.rollback(store, "snap-1", ap)
    assert restored == ["e-1"]
    assert store.entries["e-1"].content == "Good policy"


def test_purge_with_valid_approval_deletes():
    store = store_with()
    gate, agent = gated_recovery()
    ap = approval()
    gate.issue(ap)
    assert agent.purge(store, "e-9", ap) == "e-9"
    assert "e-9" not in store.entries


def test_purge_bypass_blocked():
    store = store_with()
    _, agent = gated_recovery()
    with pytest.raises(GateDenied, match="bypass"):
        agent.purge(store, "e-9", None)
    assert "e-9" in store.entries


def test_purge_reject_blocked():
    store = store_with()
    gate, agent = gated_recovery()
    ap = approval(consent_text="No")
    gate.issue(ap)
    with pytest.raises(GateDenied):
        agent.purge(store, "e-9", ap)
    assert "e-9" in store.entries


def test_purge_absent_approval_blocked():
    store = store_with()
    _, agent = gated_recovery()
    with pytest.raises(GateDenied, match="absent"):
        agent.purge(store, "e-9", approval())  # never issued to this gate
    assert "e-9" in store.entries


def test_purge_expired_blocked():
    store = store_with()
    store.step = 20
    gate, agent = gated_recovery()
    ap = approval(expires_step=5)
    gate.issue(ap)
    with pytest.raises(GateDenied, match="expired"):
        agent.purge(store, "e-9", ap)
    assert "e-9" in store.entries


def test_purge_low_confidence_blocked():
    store = store_with()
    gate, agent = gated_recovery()
    ap = approval(confidence=0.4)
    gate.issue(ap)
    with pytest.raises(GateDenied, match="low-confidence"):
        agent.purge(store, "e-9", ap)
    assert "e-9" in store.entries


def test_purge_self_contradicting_consent_blocked():
    store = store_with()
    gate, agent = gated_recovery()
    ap = approval(consent_text="yes, wait, no")
    gate.issue(ap)
    with pytest.raises(GateDenied, match="contradicting"):
        agent.purge(store, "e-9", ap)
    assert "e-9" in store.entries


def test_approval_single_use_only():
    store = store_with()
    store.add(MemoryEntry("e-10", "k2", "other", "src", 1, "trusted", 0, 0))
    gate, agent = gated_recovery()
    ap = approval()
    gate.issue(ap)
    agent.purge(store, "e-9", ap)
    # Same token object already consumed: reuse must fail.
    with pytest.raises(GateDenied, match="already used"):
        agent.purge(store, "e-10", ap)
    assert "e-10" in store.entries


def test_approval_scope_mismatch_blocked():
    store = store_with()
    gate, agent = gated_recovery()
    ap = approval(scope="purge:someone-else")
    gate.issue(ap)
    with pytest.raises(GateDenied, match="scope"):
        agent.purge(store, "e-9", ap)


def test_approval_requires_named_approver():
    gate, _ = gated_recovery()
    with pytest.raises(GateDenied, match="named approver"):
        gate.issue(approval(approver=""))


def test_rollback_bypass_blocked():
    store = MemoryStore()
    store.snapshot("snap-1")
    _, agent = gated_recovery()
    with pytest.raises(GateDenied, match="bypass"):
        agent.rollback(store, "snap-1", None)


def test_rollback_expired_blocked():
    store = MemoryStore()
    store.snapshot("snap-1")
    store.step = 99
    gate, agent = gated_recovery()
    ap = approval(token="tok-rb2", scope="rollback:snap-1", expires_step=1)
    gate.issue(ap)
    with pytest.raises(GateDenied, match="expired"):
        agent.rollback(store, "snap-1", ap)


def test_rollback_contradictory_blocked():
    store = MemoryStore()
    store.snapshot("snap-1")
    gate, agent = gated_recovery()
    ap = approval(token="tok-rb3", scope="rollback:snap-1",
                  consent_text="yes, wait, no")
    gate.issue(ap)
    with pytest.raises(GateDenied, match="contradicting"):
        agent.rollback(store, "snap-1", ap)
