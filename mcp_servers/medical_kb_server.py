"""
Medical Knowledge Base — MCP Server
-------------------------------------
Exposes two tools to agents via the Model Context Protocol:
  - symptom_lookup  : maps symptom keywords to possible conditions
  - red_flag_check  : checks if any red-flag emergency symptoms are present

In production this would connect to a curated medical ontology (e.g. SNOMED CT
or a licensed symptom API). For the demo we use a local JSON knowledge base.

Day 2 course concept: MCP server implementation.
"""

import json
from pathlib import Path
from mcp.server import MCPServer, tool

# ---------------------------------------------------------------------------
# Knowledge base (simplified — extend for production)
# ---------------------------------------------------------------------------
SYMPTOM_MAP = {
    "chest pain": {
        "conditions": ["angina", "myocardial infarction", "pulmonary embolism", "GERD"],
        "urgency_hint": "EMERGENCY",
    },
    "shortness of breath": {
        "conditions": ["asthma", "COPD exacerbation", "heart failure", "pulmonary embolism"],
        "urgency_hint": "URGENT",
    },
    "headache": {
        "conditions": ["tension headache", "migraine", "hypertensive crisis", "meningitis"],
        "urgency_hint": "ROUTINE",
    },
    "fever": {
        "conditions": ["viral infection", "bacterial infection", "COVID-19", "dengue"],
        "urgency_hint": "ROUTINE",
    },
    "severe abdominal pain": {
        "conditions": ["appendicitis", "gallstones", "kidney stones", "peritonitis"],
        "urgency_hint": "URGENT",
    },
    "loss of consciousness": {
        "conditions": ["syncope", "seizure", "cardiac arrest", "hypoglycaemia"],
        "urgency_hint": "EMERGENCY",
    },
    "slurred speech": {
        "conditions": ["stroke", "TIA", "hypoglycaemia", "intoxication"],
        "urgency_hint": "EMERGENCY",
    },
    "rash": {
        "conditions": ["allergic reaction", "eczema", "meningococcal disease", "chickenpox"],
        "urgency_hint": "ROUTINE",
    },
}

RED_FLAGS = [
    "chest pain",
    "loss of consciousness",
    "slurred speech",
    "facial drooping",
    "arm weakness",
    "severe bleeding",
    "difficulty breathing",
    "anaphylaxis",
    "suspected poisoning",
    "suicidal ideation",
]


# ---------------------------------------------------------------------------
# MCP tool definitions
# ---------------------------------------------------------------------------

app = MCPServer(name="medical_kb", version="1.0.0")


@app.tool(
    name="symptom_lookup",
    description="Look up possible conditions and urgency hint for a given symptom keyword.",
    input_schema={
        "type": "object",
        "properties": {
            "symptom": {"type": "string", "description": "A single symptom keyword or phrase"},
        },
        "required": ["symptom"],
    },
)
def symptom_lookup(symptom: str) -> dict:
    """Return possible conditions and urgency hint for a symptom."""
    key = symptom.lower().strip()
    # Fuzzy match: check if any known key is a substring of the query
    for kb_key, data in SYMPTOM_MAP.items():
        if kb_key in key or key in kb_key:
            return {"symptom": kb_key, **data, "found": True}
    return {
        "symptom": symptom,
        "conditions": ["unknown — please consult a doctor"],
        "urgency_hint": "ROUTINE",
        "found": False,
    }


@app.tool(
    name="red_flag_check",
    description="Check a list of symptoms for any emergency red flags.",
    input_schema={
        "type": "object",
        "properties": {
            "symptoms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of symptom strings to check",
            },
        },
        "required": ["symptoms"],
    },
)
def red_flag_check(symptoms: list[str]) -> dict:
    """Return any red-flag emergency symptoms found in the input list."""
    found_flags = []
    for symptom in symptoms:
        s = symptom.lower()
        for flag in RED_FLAGS:
            if flag in s:
                found_flags.append(flag)

    return {
        "red_flags_found": list(set(found_flags)),
        "is_emergency": len(found_flags) > 0,
    }


if __name__ == "__main__":
    # Run as a standalone MCP server process
    # Antigravity / agents-cli will spawn this automatically
    app.run(transport="stdio")
