# Implementation guide

## Adopting this pattern

1. Model every memory write as an entry with a source, a trust level,
   and a version. Without provenance, poisoned-entry detection has
   nothing to stand on.
2. Snapshot before any bulk ingest or model-driven memory update.
   Snapshots are what make rollback possible; without one, recovery
   is reconstruction, not restoration.
3. Run the monitor on a schedule and after every ingest batch, not
   only when something looks wrong.
4. Quarantine on detection, before seeking approval. The window
   between detection and human approval is exactly when a suspect
   entry would otherwise keep being retrieved.
5. Gate every destructive action. Keep approvals named-person,
   single-use, scoped, and expiring, and reject contradictory consent.
6. Audit everything through a hash chain, and verify the chain as
   part of the "clean" verdict — not as an afterthought.
7. Measure: findings by class, quarantine counts, recovery counts,
   post-recovery scan results. A recovery without a clean post-scan
   is not done.

## Extending the detectors

Add a detector function in `monitor.py` returning `Finding | None`,
wire it into `MemoryMonitorAgent.scan()`, and add at least one
positive and one clean-negative test. Keep detectors deterministic
and threshold-documented; a detector whose threshold nobody can
explain is a liability.
