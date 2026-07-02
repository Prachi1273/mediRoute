"""
Triage Agent
------------
Classifies symptom urgency into one of three levels:
  - EMERGENCY  → call 112/911 immediately
  - URGENT     → urgent care / ER within 2-4 hours
  - ROUTINE    → GP appointment within days

Uses the Medical KB MCP server for symptom-to-condition mapping.
Loads triage SKILL.md on demand (Day 3: agent skills concept).
"""

from google.adk.agents import Agent
from google.adk.tools.mcp import MCPTool

TRIAGE_SYSTEM_PROMPT = """
You are a medical triage specialist agent. Your ONLY job is to assess
symptom urgency. You do NOT diagnose, prescribe, or recommend treatments.

## Output schema (always return valid JSON)
{
  "urgency": "EMERGENCY" | "URGENT" | "ROUTINE",
  "confidence": 0.0–1.0,
  "flag_reason": "brief explanation",
  "red_flags": ["list of concerning symptoms found"],
  "recommend_emergency_services": true | false
}

## Urgency rules
EMERGENCY (recommend_emergency_services = true):
  Chest pain, difficulty breathing, stroke signs (FAST), severe bleeding,
  loss of consciousness, anaphylaxis, suspected poisoning.

URGENT:
  High fever (>39°C), severe pain, suspected fractures, moderate injuries,
  worsening chronic condition symptoms.

ROUTINE:
  Mild cold/flu, minor cuts, routine prescription refills, stable chronic
  condition check-ups.

Always err on the side of higher urgency when uncertain.
Do NOT output anything other than the JSON schema above.
"""


def triage_agent() -> Agent:
    """Build the triage sub-agent with Medical KB MCP tool attached."""
    return Agent(
        name="triage_agent",
        model="gemini-1.5-flash",
        system_prompt=TRIAGE_SYSTEM_PROMPT,
        tools=[
            # Medical KB MCP server (see mcp_servers/medical_kb_server.py)
            MCPTool(server_name="medical_kb", tool_name="symptom_lookup"),
            MCPTool(server_name="medical_kb", tool_name="red_flag_check"),
        ],
        # Load triage SKILL.md only when this agent is invoked
        skill="skills/triage/SKILL.md",
    )
