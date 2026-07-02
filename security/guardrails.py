"""
Security Guardrails — Day 4 course concept
------------------------------------------
Implements two security pillars:

1. sanitise_pii()   — strips / masks PII before any agent processes input
2. hitl_gate()      — human-in-the-loop check before medication advice leaves
                      the system

These run at the orchestrator boundary so no sub-agent ever receives or
emits raw PII or unsupervised medication guidance.
"""

import re
import logging
from typing import Any

logger = logging.getLogger("mediRoute.security")

# ---------------------------------------------------------------------------
# PII patterns to redact (extend this list for production)
# ---------------------------------------------------------------------------
_PII_PATTERNS = [
    # Indian Aadhaar number (12 digits)
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAAR_REDACTED]"),
    # Indian PAN card
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN_REDACTED]"),
    # Generic phone numbers
    (re.compile(r"\b(\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b"), "[PHONE_REDACTED]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),
    # Street addresses (simple heuristic — "123 Something Street/Road/Ave")
    (re.compile(r"\b\d+\s+[\w\s]+(?:street|road|avenue|lane|nagar|colony|sector)\b", re.IGNORECASE), "[ADDRESS_REDACTED]"),
]

# Keywords that suggest medication dosage guidance — triggers HITL flag
_MEDICATION_DOSAGE_PATTERNS = [
    re.compile(r"\b\d+\s?mg\b", re.IGNORECASE),
    re.compile(r"\btake\s+\d+\s+tablet", re.IGNORECASE),
    re.compile(r"\bdose\s+of\s+\d+", re.IGNORECASE),
    re.compile(r"\bprescrib", re.IGNORECASE),
    re.compile(r"\badminister\s+\d+", re.IGNORECASE),
]


def sanitise_pii(user_input: dict) -> dict:
    """
    Walk every string value in user_input and redact known PII patterns.
    Returns a new dict — never mutates the original.

    Security concept: ephemeral sandboxing — the raw PII never enters
    agent context or logs.
    """
    clean = {}
    for key, value in user_input.items():
        if isinstance(value, str):
            redacted = value
            for pattern, replacement in _PII_PATTERNS:
                redacted = pattern.sub(replacement, redacted)
            clean[key] = redacted
            if redacted != value:
                logger.info("PII redacted in field '%s'", key)
        elif isinstance(value, dict):
            # Recurse into nested dicts (e.g. location is fine, but future fields may not be)
            clean[key] = sanitise_pii(value)
        else:
            clean[key] = value

    return clean


def hitl_gate(agent_response: Any) -> dict:
    """
    Human-in-the-loop gate — Day 4 core concept.

    Scans the agent response for any medication dosage language.
    If found:
      - Sets hitl_required = True
      - Redacts the dosage from the response visible to the user
      - Adds a note directing the user to confirm with a doctor

    In a production system this would pause execution and send the
    flagged content to a doctor dashboard for approval before release.
    """
    response_text = str(agent_response)
    flagged_snippets = []

    for pattern in _MEDICATION_DOSAGE_PATTERNS:
        matches = pattern.findall(response_text)
        if matches:
            flagged_snippets.extend(matches)

    if flagged_snippets:
        logger.warning(
            "HITL gate triggered — medication language detected: %s",
            flagged_snippets,
        )
        # In production: send to doctor dashboard and PAUSE response.
        # For demo: redact and add disclaimer.
        for pattern in _MEDICATION_DOSAGE_PATTERNS:
            response_text = pattern.sub("[REQUIRES DOCTOR APPROVAL]", response_text)

        return {
            "response": response_text,
            "hitl_required": True,
            "hitl_reason": "Medication dosage guidance detected. A doctor must review before this is shared.",
            "flagged_content": flagged_snippets,
        }

    return {
        "response": agent_response,
        "hitl_required": False,
    }


def validate_location(location: dict) -> bool:
    """
    Validate that a location dict has plausible lat/lng values.
    Prevents prompt injection via malformed location strings.
    """
    try:
        if "lat" not in location or "lng" not in location:
            return False
        lat = float(location["lat"])
        lng = float(location["lng"])
        return -90 <= lat <= 90 and -180 <= lng <= 180
    except (TypeError, ValueError):
        return False
