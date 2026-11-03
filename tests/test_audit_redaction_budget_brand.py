"""Audit, redaction, budget, and brand-check tests."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_memory_defense import (
    BLOCKLIST_HASHES, MemoryStore, check_brand, contains_pii,
    estimate_cost, redact, validate_budget,
)
from agent_memory_defense.audit import AuditLog


def test_audit_chain_verifies():
    log = AuditLog()
    log.append("add", "e-1", "system")
    log.append("quarantine", "e-1", "quarantine-agent")
    assert log.verify() is True


def test_audit_tamper_breaks_verification():
    log = AuditLog()
    log.append("add", "e-1", "system")
    log.records[0]["detail"] = "tampered"
    assert log.verify() is False


def test_audit_records_actions_for_entry():
    store = MemoryStore()
    from agent_memory_defense import MemoryEntry
    store.add(MemoryEntry("e-1", "k", "content", "src", 1, "trusted", 0, 0))
    assert "add" in store.audit.actions_for("e-1")


def test_redact_email():
    out = redact("contact ana@example.com for help")
    assert "ana@example.com" not in out
    assert "[REDACTED:EMAIL]" in out


def test_redact_card_number():
    out = redact("card 4111111111111111 on file")
    assert "4111111111111111" not in out
    assert "[REDACTED:CARD]" in out


def test_redact_phone():
    out = redact("call 555-123-4567 anytime")
    assert "555-123-4567" not in out
    assert "[REDACTED:PHONE]" in out


def test_redact_ssn():
    out = redact("ssn 123-45-6789 recorded")
    assert "123-45-6789" not in out
    assert "[REDACTED:SSN]" in out


def test_redact_leaves_clean_text_untouched():
    text = "Refunds are issued within 30 days with a receipt."
    assert redact(text) == text
    assert contains_pii(text) is False


def test_contains_pii_detects_email_and_card():
    assert contains_pii("reach me at bob@example.org") is True
    assert contains_pii("card 4111111111111111") is True


def test_budget_negative_rejected():
    with pytest.raises(ValueError, match="negative"):
        validate_budget(-5.0)


def test_budget_zero_allowed():
    assert validate_budget(0.0) == 0.0


def test_estimate_cost_negative_rate_rejected():
    with pytest.raises(ValueError, match="negative"):
        estimate_cost(10, -0.5)


def test_estimate_cost_computes():
    assert estimate_cost(40, 0.25) == 10.0


def test_brand_blocklist_non_empty():
    assert len(BLOCKLIST_HASHES) > 0


def test_brand_check_flags_hashed_token():
    flagged = check_brand("we use example-blocked-brand-alpha here")
    assert flagged == ["example-blocked-brand-alpha"]


def test_brand_check_clean_text_no_flags():
    assert check_brand("Zelvermere Systems support assistant") == []


def test_brand_check_empty_blocklist_asserts():
    with pytest.raises(AssertionError):
        check_brand("anything", blocklist=frozenset())
