"""
MediRoute Orchestrator Agent
----------------------------
The top-level ADK agent that receives a user health query, fans out to
four specialist sub-agents, applies the security / HITL gate, and
returns a consolidated health-navigation response.

Course concepts demonstrated:
  - Multi-agent system with ADK (this file)
  - Agent skills via SKILL.md progressive disclosure
  - Security: PII sanitisation + human-in-the-loop gate
"""

import os
from google.adk.agents import Agent, AgentContext
from google.adk.runners import Runner

from agents.triage_agent import triage_agent
from agents.document_agent import document_agent
from agents.care_finder_agent import care_finder_agent
from agents.summary_agent import summary_agent
from security.guardrails import sanitise_pii, hitl_gate

# ---------------------------------------------------------------------------
# Orchestrator system prompt (loads triage SKILL.md on demand — Day 3 concept)
# ---------------------------------------------------------------------------
ORCHESTRATOR_SYSTEM_PROMPT = """
You are MediRoute, an AI health-navigation assistant.
Your job is to coordinate four specialist agents to help a user understand
their symptoms, find appropriate care, and prepare for their doctor visit.

## Workflow
1. Sanitise and validate the user input (remove PII before logging).
2. Run the triage_agent to classify urgency (emergency / urgent / routine).
3. If the user uploaded a medical history PDF, run document_agent in parallel.
4. Run care_finder_agent with the user's location and urgency level.
5. Run summary_agent to produce a concise doctor-visit brief.
6. Apply the HITL gate — NEVER include medication dosage recommendations
   without explicit doctor approval.
7. Return a structured response:
     - Urgency level (color-coded)
     - Recommended care pathway (ER / urgent care / clinic / telehealth)
     - Top 3 nearby facilities with distance and wait time
     - Doctor-visit brief (symptoms, history highlights, questions to ask)
     - Follow-up reminder schedule

## Hard rules (security layer)
- Do NOT store raw PII beyond the session.
- Do NOT recommend specific medications or dosages.
- Always surface the HITL gate output before medication advice.
- If urgency == "emergency", immediately surface emergency services (112/911)
  before any other information.
"""


def build_orchestrator() -> Agent:
    """Build and return the MediRoute orchestrator agent."""
    orchestrator = Agent(
        name="mediRoute_orchestrator",
        model="gemini-1.5-flash",          # free-tier friendly
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        sub_agents=[
            triage_agent(),
            document_agent(),
            care_finder_agent(),
            summary_agent(),
        ],
        # Skills are loaded on-demand (Day 3: agent skills / SKILL.md pattern)
        skills_dir="skills/",
        tools=[],                           # tools come from MCP servers (see mcp_servers/)
    )
    return orchestrator


async def run_mediRoute(user_input: dict) -> dict:
    """
    Entry point called by the FastAPI server or CLI.

    user_input schema:
    {
        "symptoms": str,
        "location": {"lat": float, "lng": float},
        "pdf_path": str | None,   # optional medical history
        "age": int | None,
        "user_id": str            # session token, never a real name
    }
    """
    # Step 1: Sanitise PII before any agent sees the raw input
    clean_input = sanitise_pii(user_input)

    orchestrator = build_orchestrator()
    runner = Runner(agent=orchestrator)

    ctx = AgentContext(
        user_message=str(clean_input),
        session_id=clean_input["user_id"],
    )

    raw_response = await runner.run_async(ctx)

    # Step 2: HITL gate — flag any medication content for doctor review
    final_response = hitl_gate(raw_response)

    return final_response


# ---------------------------------------------------------------------------
# CLI entry point (useful for local testing & Antigravity demos)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio, json

    sample = {
        "symptoms": "Chest tightness and shortness of breath for 2 hours",
        "location": {"lat": 18.5204, "lng": 73.8567},  # Pune
        "pdf_path": None,
        "age": 42,
        "user_id": "session_abc123",
    }

    result = asyncio.run(run_mediRoute(sample))
    print(json.dumps(result, indent=2))
