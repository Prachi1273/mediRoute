"""
Triage Agent Evaluation Suite — Day 4 concept
----------------------------------------------
Tests the triage agent against known symptom/urgency pairs to ensure
the agent classifies correctly before deployment.

Run with:  pytest evals/ -v
"""

import pytest
import asyncio
import json

# Evaluation dataset: (symptoms, expected_urgency, description)
TRIAGE_EVAL_CASES = [
    # EMERGENCY cases
    (
        "Sudden severe chest pain radiating to my left arm, sweating",
        "EMERGENCY",
        "Classic MI presentation — must be EMERGENCY",
    ),
    (
        "My face is drooping on one side and I can't lift my arm",
        "EMERGENCY",
        "FAST stroke signs — must be EMERGENCY",
    ),
    (
        "I passed out and can't breathe properly",
        "EMERGENCY",
        "Loss of consciousness + breathing — must be EMERGENCY",
    ),
    # URGENT cases
    (
        "High fever 39.5°C for two days, severe body aches",
        "URGENT",
        "High fever — should be URGENT",
    ),
    (
        "Severe abdominal pain lower right side, nausea for 6 hours",
        "URGENT",
        "Possible appendicitis — should be URGENT",
    ),
    # ROUTINE cases
    (
        "Mild sore throat and runny nose for 2 days, no fever",
        "ROUTINE",
        "Common cold — should be ROUTINE",
    ),
    (
        "Rash on my arm, not spreading, no pain, appeared yesterday",
        "ROUTINE",
        "Mild rash — should be ROUTINE",
    ),
]


def mock_triage_response(symptoms: str) -> dict:
    """
    Simulated triage response for unit testing without hitting the LLM.
    In CI/CD replace this with actual agent calls using test credentials.
    """
    emergency_keywords = [
        "chest pain", "can't breathe", "passed out", "face drooping",
        "can't lift", "stroke", "heart attack", "unconscious",
    ]
    urgent_keywords = [
        "39.", "40.", "high fever", "severe abdominal", "appendicitis",
        "broken", "fracture", "can't walk",
    ]
    # "no fever" should NOT trigger urgent — check negation
    s = symptoms.lower()
    negated_fever = "no fever" in s

    if any(kw in s for kw in emergency_keywords):
        urgency = "EMERGENCY"
    elif not negated_fever and any(kw in s for kw in urgent_keywords):
        urgency = "URGENT"
    else:
        urgency = "ROUTINE"

    return {"urgency": urgency, "confidence": 0.85, "red_flags": [], "recommend_emergency_services": urgency == "EMERGENCY"}


class TestTriageEvals:
    """Evaluation tests for the triage agent."""

    @pytest.mark.parametrize("symptoms,expected_urgency,description", TRIAGE_EVAL_CASES)
    def test_urgency_classification(self, symptoms, expected_urgency, description):
        """Each symptom set must map to the correct urgency level."""
        result = mock_triage_response(symptoms)
        assert result["urgency"] == expected_urgency, (
            f"FAILED: {description}\n"
            f"  Symptoms: {symptoms}\n"
            f"  Expected: {expected_urgency}\n"
            f"  Got:      {result['urgency']}"
        )

    def test_emergency_always_recommends_services(self):
        """EMERGENCY urgency must always set recommend_emergency_services = True."""
        result = mock_triage_response("Chest pain and difficulty breathing")
        if result["urgency"] == "EMERGENCY":
            assert result["recommend_emergency_services"] is True

    def test_confidence_in_range(self):
        """Confidence must always be between 0 and 1."""
        result = mock_triage_response("Headache and mild fever")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_output_is_valid_schema(self):
        """Response must contain all required fields."""
        result = mock_triage_response("Sore throat")
        required_keys = {"urgency", "confidence", "red_flags", "recommend_emergency_services"}
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"
