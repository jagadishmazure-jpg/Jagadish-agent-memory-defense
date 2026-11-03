# ADR 001 — Snapshot rollback over in-place repair

## Decision

Recovery restores a prior good snapshot rather than editing suspect
entries in place.

## Rationale

In-place repair of a poisoned store risks preserving the poison in a
new form and leaves no clean reference state. A snapshot gives a
known-good state to return to, and the rollback itself is audited.

## Consequence

Entries created after the snapshot are not deleted by rollback; they
remain quarantined until a gated purge removes them.
