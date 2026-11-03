"""Run the poisoned-memory demo scenario and print its metrics.

All data is synthetic; the operator is the fictional Zelvermere Systems.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_memory_defense import Approval, build_demo_store, run_cycle


def main() -> None:
    store, baselines, snapshot_id = build_demo_store()
    approval = Approval(
        approver="Priya Nair", token="demo-report-1",
        scope=f"rollback:{snapshot_id}", expires_step=10,
        confidence=1.0, consent_text="yes",
    )
    metrics = run_cycle(store, baselines, rollback_approval=approval,
                        snapshot_id=snapshot_id)
    print("demo metrics:")
    for key in ("findings", "by_class", "quarantined", "rolled_back",
                "post_scan_findings", "audit_valid", "clean"):
        print(f"  {key}: {metrics[key]}")
    print(f"  active entries after recovery: {len(store.active_entries())}")
    print(f"  quarantined entries after recovery: {len(store.quarantined_entries())}")


if __name__ == "__main__":
    main()
