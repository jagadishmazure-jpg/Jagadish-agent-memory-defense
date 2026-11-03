# ADR 002 — Quarantine before approval

## Decision

Suspect entries are quarantined immediately on detection, before any
human approval is sought for recovery.

## Rationale

The window between detection and approval is exactly when a suspect
entry would otherwise keep being retrieved and shaping answers.
Isolation is reversible (release) and non-destructive, so it needs no
gate itself.

## Consequence

Quarantine is an audited mutation; a wrongly quarantined entry is
visible in the audit log and recoverable by release or rollback.
