# Architecture

## Components

- `models.py` — `MemoryEntry`, `Finding`, `Snapshot`, `Retrieval`,
  and the six-class taxonomy constants.
- `store.py` — entries, snapshots (deep copies of active entries),
  quarantine flags, and audit appends on every mutation.
- `monitor.py` — one deterministic detector per failure class, plus
  conflict detection across entries.
- `agents.py` — `MemoryMonitorAgent` (scan), `QuarantineAgent`
  (isolate/release), `RecoveryAgent` (gated purge/rollback, ungated
  re-grounding).
- `gates.py` — `HumanGate` and consent parsing.
- `audit.py` — SHA-256 hash-chained, append-only log with `verify()`.
- `redaction.py` — PII redaction for phone, SSN, card, email.
- `budget_brand.py` — non-negative budget validation; hashed
  brand blocklist.
- `pipeline.py` — `run_cycle()`: detect -> quarantine -> gated
  rollback -> post-scan verification, returning measurement metrics.
- `demo_data.py` — synthetic Zelvermere Systems scenario.

## Key decisions

See `docs/adr/` for: snapshot-based rollback over in-place repair,
quarantine-before-approval, strict consent parsing, and hash-chained
audit over plain logging.
