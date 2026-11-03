"""PII redaction for memory content and audit details.

The checklist covers phone numbers, SSNs, card numbers, and email
addresses. Anything matching is replaced with a typed placeholder so
logs and reports never carry raw personal data.
"""
from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s])\d{3}[-.\s]\d{4}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _card_replacement(match: "re.Match[str]") -> str:
    digits = re.sub(r"\D", "", match.group(0))
    if 13 <= len(digits) <= 19 and _luhn_ok(digits):
        return "[REDACTED:CARD]"
    return match.group(0)


def redact(text: str) -> str:
    """Redact email, SSN, phone, and card numbers from *text*."""
    out = EMAIL_RE.sub("[REDACTED:EMAIL]", text)
    out = SSN_RE.sub("[REDACTED:SSN]", out)
    out = PHONE_RE.sub("[REDACTED:PHONE]", out)
    out = CARD_RE.sub(_card_replacement, out)
    return out


def contains_pii(text: str) -> bool:
    return redact(text) != text
