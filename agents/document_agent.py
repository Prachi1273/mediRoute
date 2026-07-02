"""
Document Parser Agent
---------------------
Extracts structured medical history from an uploaded PDF.
Handles lab reports, prescription history, discharge summaries, etc.

Uses the PDF Parser MCP server.
PII (name, address, insurance number) is redacted before passing
extracted data to other agents — security pillar (Day 4).
"""

from google.adk.agents import Agent
from google.adk.tools.mcp import MCPTool

DOCUMENT_SYSTEM_PROMPT = """
You are a medical document extraction specialist. Given a patient's medical
history PDF (already text-extracted), pull out the following structured data:

## Output schema (always return valid JSON)
{
  "conditions": ["list of diagnosed conditions"],
  "medications": ["current medications — name and dosage"],
  "allergies": ["known allergies"],
  "recent_labs": [{"test": str, "value": str, "date": str}],
  "surgeries": ["past procedures with approximate date"],
  "notes": "any clinically relevant free-text observations"
}

## Rules
- Redact all PII: patient name → "[PATIENT]", DOB → "[DOB]", 
  address → "[ADDRESS]", insurance ID → "[ID]".
- If a field is not found in the document, return an empty list / null.
- Never invent data that is not in the document.
- Output ONLY the JSON schema above, no preamble.
"""


def document_agent() -> Agent:
    """Build the document parser sub-agent."""
    return Agent(
        name="document_agent",
        model="gemini-1.5-flash",
        system_prompt=DOCUMENT_SYSTEM_PROMPT,
        tools=[
            # PDF Parser MCP server (see mcp_servers/pdf_parser_server.py)
            MCPTool(server_name="pdf_parser", tool_name="extract_text"),
            MCPTool(server_name="pdf_parser", tool_name="extract_tables"),
        ],
        skill="skills/document/SKILL.md",
    )
