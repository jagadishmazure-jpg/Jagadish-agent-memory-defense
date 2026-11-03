# Knowledge notes: defending agent memory

Distilled design notes for this repo, written in original prose. The
demo operator is the fictional Zelvermere Systems; all examples are
synthetic.

## Why memory fails differently from other data

Agent memory is read back into prompts, so a bad entry does not just
sit in a table — it shapes the next answer, and the next answer can be
written back as a new memory. That feedback loop is why memory needs
its own failure taxonomy rather than borrowing a generic data-quality
checklist: the failure is not only "wrong value" but "wrong value that
will be repeated with confidence".

## The six classes, and what each one teaches

- **Poisoned entries** are the security class. The tell is provenance
  plus language: an untrusted source plus directive wording. Detection
  leans on provenance because content alone is unreliable — a poisoned
  entry can read perfectly normally.
- **Drift** is the change-management class. Memory should change only
  through approved updates; an unapproved material change is a finding
  even if the new text looks plausible. Baselines (the snapshot) are
  what make drift detectable at all.
- **Context stuffing** is the capacity class. An entry that balloons
  crowds out everything retrieved alongside it, so size and filler
  ratio are legitimate quality signals.
- **Retrieval hallucination** is the citation class. If a retrieval
  result cites a source id the store has never held, the retrieval
  layer — not the entry — is at fault, and the fix belongs there.
- **Conflicts** are the consistency class. One key, two incompatible
  active values means at least one write path skipped validation.
- **Cache staleness** is the freshness class. Time-to-live and source
  version are both needed: a value can be young but already superseded,
  or current-version but ancient.

## The recovery order matters

Detect first, quarantine second, recover third. Quarantine exists
because recovery needs a human, and humans are slow: between detection
and approval, the suspect entry must not be retrievable. Rollback
restores a known-good snapshot rather than editing entries by hand,
because hand-editing a poisoned store risks preserving the poison in
a new form. Re-grounding — replacing content from a trusted source —
is the non-destructive alternative when the source is available.

## Why the gate is strict

Destructive recovery can destroy evidence and good data alike, so the
approval is named-person (accountability), single-use (no replay),
scoped (no broader action than approved), and expiring (no stale
approvals). Consent parsing rejects self-contradiction outright:
"yes, wait, no" is not a yes with noise, it is a signal the approver
is unsure, and unsure approvals must not destroy data. Low-confidence
approvals are rejected for the same reason.
