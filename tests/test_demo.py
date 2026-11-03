"""End-to-end demo tests: poisoned entry -> quarantine -> rollback -> clean."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_memory_defense import (
    Approval, GateDenied, build_demo_store, run_cycle,
)
from agent_memory_defense.agents import MemoryMonitorAgent
from agent_memory_defense.demo_data import (
    GOOD_HELP_ARTICLE, GOOD_REFUND_POLICY, GOOD_SHIPPING_CUTOFF, POISONED_CONTENT,
)


def test_demo_poisoned_entry_detected():
    store, baselines, _ = build_demo_store()
    findings = MemoryMonitorAgent().scan(store, baselines)
    poisoned = [f for f in findings if f.failure_class == "poisoned"]
    assert len(poisoned) == 1
    assert poisoned[0].entry_id == "e-9"


def test_demo_cycle_quarantines_and_rolls_back_to_clean():
    store, baselines, snapshot_id = build_demo_store()
    approval = Approval(
        approver="Priya Nair", token="demo-rb-1",
        scope=f"rollback:{snapshot_id}", expires_step=10,
        confidence=1.0, consent_text="yes",
    )
    metrics = run_cycle(store, baselines, rollback_approval=approval,
                        snapshot_id=snapshot_id)
    assert metrics["findings"] >= 2
    assert metrics["by_class"].get("poisoned", 0) == 1
    assert metrics["by_class"].get("conflict", 0) == 1
    assert metrics["quarantined"] == ["e-9", "e-1"]
    assert metrics["rolled_back"] == ["e-1", "e-2", "e-3"]
    assert metrics["post_scan_findings"] == 0
    assert metrics["audit_valid"] is True
    assert metrics["clean"] is True


def test_demo_memory_verified_clean_afterwards():
    store, baselines, snapshot_id = build_demo_store()
    approval = Approval(
        approver="Priya Nair", token="demo-rb-2",
        scope=f"rollback:{snapshot_id}", expires_step=10,
        confidence=1.0, consent_text="yes",
    )
    run_cycle(store, baselines, rollback_approval=approval, snapshot_id=snapshot_id)
    active = {e.entry_id: e.content for e in store.active_entries()}
    assert active == {
        "e-1": GOOD_REFUND_POLICY,
        "e-2": GOOD_SHIPPING_CUTOFF,
        "e-3": GOOD_HELP_ARTICLE,
    }
    assert POISONED_CONTENT not in " ".join(active.values())
    assert store.entries["e-9"].quarantined is True


def test_demo_cycle_without_approval_cannot_roll_back():
    store, baselines, snapshot_id = build_demo_store()
    with pytest.raises(GateDenied, match="bypass"):
        run_cycle(store, baselines, rollback_approval=None, snapshot_id=snapshot_id)
