"""Human approval gate for destructive recovery actions.

An approval is named-person, single-use, scoped to one action, and
expiring. The gate rejects: bypass (no approval supplied), rejection,
absent approval, expired approval, low-confidence approval, and
self-contradicting consent such as "yes, wait, no".
"""
from __future__ import annotations

from dataclasses import dataclass, field

YES_WORDS = ("yes", "approve", "approved", "go ahead", "proceed", "confirm")
NO_WORDS = ("no", "wait", "stop", "cancel", "hold", "reject", "not yet")


class GateDenied(Exception):
    """Raised when a gated action is not properly approved."""


def parse_consent(text: str) -> str:
    """Classify free-text consent.

    Returns "approved", "rejected", "contradictory", or "unclear".
    A message containing both a yes-word and a no-word (for example
    "yes, wait, no") is contradictory and never counts as approval.
    """
    lowered = text.lower()
    has_yes = any(w in lowered for w in YES_WORDS)
    has_no = any(w in lowered for w in NO_WORDS)
    if has_yes and has_no:
        return "contradictory"
    if has_yes:
        return "approved"
    if has_no:
        return "rejected"
    return "unclear"


@dataclass
class Approval:
    approver: str  # named person, never a role-only string
    token: str
    scope: str  # the single action this approval covers, e.g. "purge:e-9"
    expires_step: int
    confidence: float = 1.0
    consent_text: str = "yes"
    used: bool = False


@dataclass
class HumanGate:
    min_confidence: float = 0.7
    _issued: dict = field(default_factory=dict)

    def issue(self, approval: Approval) -> Approval:
        if not approval.approver or not approval.approver.strip():
            raise GateDenied("approval requires a named approver")
        self._issued[approval.token] = approval
        return approval

    def authorize(self, approval: Approval | None, scope: str, step: int) -> Approval:
        """Validate and consume an approval, or raise GateDenied."""
        if approval is None:
            raise GateDenied("bypass blocked: no approval supplied")
        stored = self._issued.get(approval.token)
        if stored is None or stored is not approval:
            raise GateDenied("absent approval: unknown approval token")
        if approval.used:
            raise GateDenied("approval already used: single-use only")
        if step > approval.expires_step:
            raise GateDenied("approval expired")
        if approval.scope != scope:
            raise GateDenied("approval scope mismatch")
        if not approval.approver or not approval.approver.strip():
            raise GateDenied("approval requires a named approver")
        consent = parse_consent(approval.consent_text)
        if consent == "contradictory":
            raise GateDenied("self-contradicting consent rejected")
        if consent != "approved":
            raise GateDenied(f"consent not approved: {consent}")
        if approval.confidence < self.min_confidence:
            raise GateDenied("low-confidence approval rejected")
        approval.used = True
        return approval
