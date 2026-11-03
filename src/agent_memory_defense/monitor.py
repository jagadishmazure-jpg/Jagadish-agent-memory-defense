"""Detection rules for the six memory failure classes.

Each detector is deterministic and works on synthetic data only.
Thresholds are documented constants, not tuned claims.
"""
from __future__ import annotations

import re

from .models import Finding, MemoryEntry, Retrieval

# Directive phrases that an untrusted memory entry must never carry.
INJECTION_PHRASES = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "override policy",
    "disregard safety rules",
    "reveal system instructions",
)

FILLER_WORDS = ("filler", "lorem", "placeholder", "repeat")
STUFFING_TOKEN_LIMIT = 200
DRIFT_SIMILARITY_FLOOR = 0.5


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def detect_poisoned(entry: MemoryEntry) -> Finding | None:
    lowered = entry.content.lower()
    for phrase in INJECTION_PHRASES:
        if phrase in lowered:
            return Finding("poisoned", entry.entry_id, 0.95,
                           f"injection phrase present: {phrase!r}")
    if entry.trust == "untrusted" and any(
        w in lowered for w in ("override", "grant", "approve all", "bypass")
    ):
        return Finding("poisoned", entry.entry_id, 0.8,
                       "untrusted source issuing an override-style directive")
    return None


def detect_drift(entry: MemoryEntry, baseline_content: str | None) -> Finding | None:
    if baseline_content is None or entry.approved_change:
        return None
    if entry.content == baseline_content:
        return None
    similarity = _jaccard(entry.content, baseline_content)
    if similarity < DRIFT_SIMILARITY_FLOOR:
        return Finding("drift", entry.entry_id, 0.85,
                       f"unapproved change, token similarity {similarity:.2f} "
                       f"below floor {DRIFT_SIMILARITY_FLOOR}")
    return None


def detect_stuffing(entry: MemoryEntry) -> Finding | None:
    words = entry.content.split()
    if len(words) > STUFFING_TOKEN_LIMIT:
        return Finding("context_stuffing", entry.entry_id, 0.9,
                       f"{len(words)} tokens exceeds limit {STUFFING_TOKEN_LIMIT}")
    lowered = entry.content.lower()
    filler_hits = sum(lowered.count(w) for w in FILLER_WORDS)
    if words and filler_hits / len(words) > 0.5:
        return Finding("context_stuffing", entry.entry_id, 0.85,
                       "majority filler content")
    return None


def detect_hallucination(retrieval: Retrieval, known_ids: set[str]) -> Finding | None:
    unknown = [c for c in retrieval.cited_source_ids if c not in known_ids]
    if unknown:
        return Finding("retrieval_hallucination", unknown[0], 0.9,
                       f"cited source {unknown[0]!r} does not exist in the store")
    return None


def detect_conflicts(entries: list[MemoryEntry]) -> list[Finding]:
    findings: list[Finding] = []
    by_key: dict[str, list[MemoryEntry]] = {}
    for entry in entries:
        if not entry.quarantined:
            by_key.setdefault(entry.key, []).append(entry)
    for key, group in by_key.items():
        contents = {e.content.strip().lower() for e in group}
        if len(group) > 1 and len(contents) > 1:
            findings.append(Finding(
                "conflict", group[0].entry_id, 0.85,
                f"key {key!r} has {len(contents)} incompatible active values"))
    return findings


def detect_staleness(entry: MemoryEntry, current_step: int, ttl_steps: int,
                     latest_source_version: int) -> Finding | None:
    if current_step - entry.updated_step > ttl_steps:
        return Finding("cache_staleness", entry.entry_id, 0.8,
                       f"age {current_step - entry.updated_step} steps exceeds TTL {ttl_steps}")
    if entry.source_version < latest_source_version:
        return Finding("cache_staleness", entry.entry_id, 0.8,
                       f"source version {entry.source_version} behind latest {latest_source_version}")
    return None
