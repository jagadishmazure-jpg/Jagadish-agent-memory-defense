"""Core data types for agent memory defense.

All data here is synthetic and fictional. The example operator is
Zelvermere Systems, a fictional company used only as a demo tenant.
This project is an independent study project and is not affiliated
with, endorsed by, or connected to any real company.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# The six failure classes in the memory failure taxonomy.
TAXONOMY_CLASSES = (
    "poisoned",
    "drift",
    "context_stuffing",
    "retrieval_hallucination",
    "conflict",
    "cache_staleness",
)

TAXONOMY_DESCRIPTIONS = {
    "poisoned": "An entry planted or altered by an untrusted source to steer later answers.",
    "drift": "An entry whose content changed materially without an approved change record.",
    "context_stuffing": "An entry bloated with filler or repeated text that crowds out useful context.",
    "retrieval_hallucination": "A retrieval result that cites a source that does not exist in the store.",
    "conflict": "Two active entries under one key that state incompatible facts.",
    "cache_staleness": "An entry older than its time-to-live, or behind the latest source version.",
}


@dataclass
class MemoryEntry:
    """One unit of agent memory."""

    entry_id: str
    key: str
    content: str
    source: str
    source_version: int = 1
    trust: str = "trusted"  # "trusted" or "untrusted"
    created_step: int = 0
    updated_step: int = 0
    approved_change: bool = False
    quarantined: bool = False


@dataclass
class Finding:
    """One detection result from the monitor agent."""

    failure_class: str
    entry_id: str
    confidence: float  # 0.0 - 1.0
    evidence: str

    def __post_init__(self) -> None:
        if self.failure_class not in TAXONOMY_CLASSES:
            raise ValueError(f"unknown failure class: {self.failure_class}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class Snapshot:
    """A point-in-time copy of the store's active entries."""

    snapshot_id: str
    step: int
    entries: dict = field(default_factory=dict)


@dataclass
class Retrieval:
    """A retrieval result, with the source ids it claims to cite."""

    query: str
    cited_source_ids: list
    answer: str
