# Discussion points

- Why memory needs its own failure taxonomy: a bad entry is re-read
  into prompts, so errors compound instead of sitting still.
- Why quarantine precedes approval: humans are slow, and retrieval
  does not wait.
- Why "yes, wait, no" must be a rejection, not a yes: contradictory
  consent signals an unsure approver, and unsure approvals must not
  destroy data.
- Why rollback restores a snapshot instead of editing entries: hand
  repair risks preserving the poison in a new form.
- Why the audit is hash-chained: a plain log can be rewritten; a
  chain makes rewriting detectable.
- Honest limits of this repo: heuristic detectors on synthetic data,
  documented thresholds, CI not verified, no deployment.
