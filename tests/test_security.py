"""
Security Tests — Day 4 concept
--------------------------------
Tests for the PII guardrails and HITL gate.
"""

import pytest
from security.guardrails import sanitise_pii, hitl_gate, validate_location


class TestPIISanitisation:

    def test_email_is_redacted(self):
        inp = {"symptoms": "Email me at john.doe@gmail.com", "user_id": "sess_001"}
        result = sanitise_pii(inp)
        assert "john.doe@gmail.com" not in result["symptoms"]
        assert "[EMAIL_REDACTED]" in result["symptoms"]

    def test_phone_is_redacted(self):
        inp = {"symptoms": "Call me on +91-9876543210", "user_id": "sess_001"}
        result = sanitise_pii(inp)
        assert "9876543210" not in result["symptoms"]

    def test_clean_input_unchanged(self):
        inp = {"symptoms": "Chest pain for two hours", "user_id": "sess_001"}
        result = sanitise_pii(inp)
        assert result["symptoms"] == "Chest pain for two hours"

    def test_nested_dict_sanitised(self):
        inp = {"symptoms": "Headache", "meta": {"note": "email: test@x.com"}, "user_id": "sess_001"}
        result = sanitise_pii(inp)
        assert "test@x.com" not in result["meta"]["note"]

    def test_user_id_preserved(self):
        """session tokens (no PII patterns) must pass through unchanged."""
        inp = {"symptoms": "Fever", "user_id": "session_abc123xyz"}
        result = sanitise_pii(inp)
        assert result["user_id"] == "session_abc123xyz"


class TestHITLGate:

    def test_clean_response_passes(self):
        response = {"urgency": "ROUTINE", "care": "GP visit recommended"}
        result = hitl_gate(response)
        assert result["hitl_required"] is False

    def test_dosage_triggers_hitl(self):
        response = "Take 500mg of paracetamol twice daily"
        result = hitl_gate(response)
        assert result["hitl_required"] is True

    def test_prescribe_triggers_hitl(self):
        response = "I would prescribe antibiotics for this infection"
        result = hitl_gate(response)
        assert result["hitl_required"] is True

    def test_flagged_content_returned(self):
        response = "Administer 200 units of insulin"
        result = hitl_gate(response)
        assert "flagged_content" in result
        assert len(result["flagged_content"]) > 0


class TestLocationValidation:

    def test_valid_location(self):
        assert validate_location({"lat": 18.52, "lng": 73.85}) is True

    def test_invalid_lat(self):
        assert validate_location({"lat": 999, "lng": 73.85}) is False

    def test_injection_attempt(self):
        assert validate_location({"lat": "DROP TABLE users;", "lng": 0}) is False

    def test_missing_keys(self):
        assert validate_location({}) is False
