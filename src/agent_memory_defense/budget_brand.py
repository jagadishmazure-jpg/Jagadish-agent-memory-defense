"""Budget validation and brand-name check.

Budget: cost inputs must reject negatives; a zero budget is allowed
but funds nothing. Brand check: the blocklist is stored as SHA-256
hashes, never as plain names, and must be non-empty.
"""
from __future__ import annotations

import hashlib


def validate_budget(amount: float) -> float:
    if amount < 0:
        raise ValueError("budget and cost inputs must not be negative")
    return amount


def estimate_cost(num_entries: int, cost_per_entry: float) -> float:
    validate_budget(cost_per_entry)
    if num_entries < 0:
        raise ValueError("entry count must not be negative")
    return num_entries * cost_per_entry


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.strip().lower().encode("utf-8")).hexdigest()


# Hashes of placeholder tokens reserved for the operator-supplied
# production blocklist. These are synthetic placeholders, not real
# brand names; a deployment replaces this set with its own hashes.
BLOCKLIST_HASHES: frozenset[str] = frozenset({
    _hash_token("example-blocked-brand-alpha"),
    _hash_token("example-blocked-brand-beta"),
})


def check_brand(text: str, blocklist: frozenset[str] = BLOCKLIST_HASHES) -> list[str]:
    """Return flagged tokens in *text* whose hash is blocklisted."""
    assert blocklist, "brand blocklist must be non-empty"
    flagged = []
    for token in text.split():
        cleaned = token.strip(".,;:!?()[]{}\"'").lower()
        if cleaned and _hash_token(cleaned) in blocklist:
            flagged.append(cleaned)
    return flagged
