"""
Care Finder Agent
-----------------
Given a user's location and urgency level, finds the best care options:
  - EMERGENCY  → nearest hospital ER
  - URGENT     → urgent care centres + ER options
  - ROUTINE    → nearby GPs, clinics, telehealth links

Uses the Places API MCP server (Google Maps under the hood).
"""

from google.adk.agents import Agent
from google.adk.tools.mcp import MCPTool

CARE_FINDER_SYSTEM_PROMPT = """
You are a care-pathway navigator. Given an urgency level and GPS location,
find the best care options for the patient.

## Output schema (always return valid JSON)
{
  "recommended_pathway": "ER" | "URGENT_CARE" | "GP" | "TELEHEALTH",
  "facilities": [
    {
      "name": str,
      "address": str,
      "distance_km": float,
      "wait_time_mins": int | null,
      "phone": str,
      "maps_url": str,
      "open_now": bool
    }
  ],
  "telehealth_options": [
    {"name": str, "url": str, "avg_wait_mins": int}
  ],
  "emergency_numbers": {"local": str, "ambulance": str}
}

## Rules
- Return max 3 facilities, sorted by distance.
- For EMERGENCY urgency: always include ambulance number as FIRST item.
- For ROUTINE: always include at least one telehealth option.
- Prefer facilities open right now (open_now = true).
- Output ONLY the JSON schema above.
"""


def care_finder_agent() -> Agent:
    """Build the care finder sub-agent."""
    return Agent(
        name="care_finder_agent",
        model="gemini-1.5-flash",
        system_prompt=CARE_FINDER_SYSTEM_PROMPT,
        tools=[
            # Places API MCP server (see mcp_servers/places_server.py)
            MCPTool(server_name="places_api", tool_name="search_nearby"),
            MCPTool(server_name="places_api", tool_name="get_place_details"),
            MCPTool(server_name="places_api", tool_name="get_directions"),
        ],
        skill="skills/care_finder/SKILL.md",
    )
