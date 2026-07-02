"""
Summary Agent
-------------
Synthesises triage output + document history into a concise doctor-visit
brief. Also schedules follow-up reminders via the Notifier MCP server.

The doctor brief is the key deliverable users will bring to their appointment.
"""

from google.adk.agents import Agent
from google.adk.tools.mcp import MCPTool

SUMMARY_SYSTEM_PROMPT = """
You are a medical communication specialist. Synthesise the triage assessment
and extracted medical history into a clear, structured doctor-visit brief
that the patient can show their doctor.

## Output schema (always return valid JSON)
{
  "doctor_brief": {
    "chief_complaint": str,         // one sentence — the main issue
    "symptom_timeline": str,        // when symptoms started and how they changed
    "relevant_history": [str],      // relevant conditions / medications from PDF
    "questions_to_ask": [str],      // 3-5 suggested questions for the doctor
    "urgency_note": str             // gentle reminder of urgency level
  },
  "reminders": [
    {
      "type": "appointment" | "medication" | "follow_up",
      "message": str,
      "send_at": "ISO8601 datetime"
    }
  ]
}

## Rules
- Keep chief_complaint under 20 words.
- questions_to_ask must be real, useful questions — not generic placeholders.
- NEVER include medication dosage recommendations.
- If urgency is EMERGENCY, doctor_brief should lead with "SEEK EMERGENCY 
  CARE IMMEDIATELY" before any other content.
- Output ONLY the JSON schema above.
"""


def summary_agent() -> Agent:
    """Build the summary and reminder sub-agent."""
    return Agent(
        name="summary_agent",
        model="gemini-1.5-flash",
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        tools=[
            # Notifier MCP server (see mcp_servers/notifier_server.py)
            MCPTool(server_name="notifier", tool_name="schedule_reminder"),
            MCPTool(server_name="notifier", tool_name="send_email"),
            MCPTool(server_name="notifier", tool_name="send_sms"),
        ],
        skill="skills/summary/SKILL.md",
    )
