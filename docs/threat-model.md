# Threat model

## Assets

Agent memory entries, snapshots, and the audit log.

## Threats (STRIDE-style, scoped to memory)

- **Spoofing / Tampering — poisoned entries.** An untrusted ingest
  path plants directive wording. Mitigation: provenance + trust
  levels, injection-phrase and override-directive detection,
  quarantine on detection.
- **Tampering — drift.** Unapproved edits change entries silently.
  Mitigation: baseline comparison, approved-change flag, audit trail.
- **Tampering — audit forgery.** An attacker edits history to hide
  a purge or rollback. Mitigation: hash-chained audit; `verify()`
  catches edits, deletions, and reordering.
- **Repudiation — ungated destruction.** A purge with no accountable
  approver. Mitigation: named-person, single-use, scoped, expiring
  approvals; every destructive action is audited with the actor.
- **Information disclosure — PII in memory and logs.** Entries and
  audit details can carry personal data. Mitigation: redaction of
  phone, SSN, card numbers, and email addresses before logging.
- **Denial of service — stuffing.** Bloated entries crowd out useful
  context. Mitigation: token-limit and filler-ratio detection.

## Out of scope

Live model prompt-injection defense, access control to the store
itself, and encrypted storage — all assumed to be provided by the
hosting layer. Detectors here are heuristic, not adversarially robust.
