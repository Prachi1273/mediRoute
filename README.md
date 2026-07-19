# 🏥 MediRoute — AI Health Navigation Agent

> Multi-agent AI system that helps people figure out how urgent their symptoms are, where to get care, and what to tell their doctor — built on Google's Agent Development Kit (ADK) and the Model Context Protocol (MCP).

[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![Framework](https://img.shields.io/badge/Agents-Google%20ADK-0F6E56)]()
[![LLM](https://img.shields.io/badge/LLM-Gemini%201.5%20Flash-4285F4)]()
[![API](https://img.shields.io/badge/API-FastAPI-009688)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]()


---

## Description

MediRoute is a multi-agent AI system that helps people navigate the healthcare system the moment they start feeling unwell — usually the most confusing and highest-anxiety point in any care journey. A user describes their symptoms, shares their location, and optionally uploads a medical history PDF. Four coordinated AI agents then work together behind a security layer to return:

- **Urgency classification** — Emergency / Urgent / Routine
- **Nearby care options** — ER, urgent care, GP, or telehealth
- **A doctor-visit brief** — a clear, structured summary the patient can bring to their appointment
- **Follow-up reminders** — appointment and check-in reminders via email/SMS

The whole system is designed around a simple principle: **AI can help someone decide what to do next, but it should never replace a doctor** — which is why every response passes through explicit security and human-in-the-loop gates before it reaches the user.

## Problem Statement

When someone feels unwell, they typically face three overlapping problems at once:

1. **"How serious is this?"** — Most people either panic over minor symptoms or dangerously underestimate serious ones, because they have no easy way to triage themselves.
2. **"Where do I even go?"** — ER, urgent care, a GP, or a video consult all serve different needs, but people default to whichever is most familiar (usually the most expensive or the most crowded).
3. **"What do I tell the doctor?"** — Appointments are short, and patients often forget key details, timelines, or the right questions to ask, walking out with less clarity than they walked in with.

Existing symptom checkers either stop at a vague "see a doctor" recommendation or, worse, veer into unsupervised medical advice. MediRoute is built to close that gap safely — combining urgency triage, care routing, and doctor-visit preparation into a single guided flow, with hard safety rules that prevent it from ever acting like an unsupervised prescriber.

## Features

- 🚨 **Symptom-based urgency triage** — classifies input into Emergency / Urgent / Routine using a red-flag symptom knowledge base, always erring toward higher urgency when uncertain
- 📍 **Location-aware care routing** — finds and ranks the top 3 nearby facilities by distance and live wait/open status, with dedicated telehealth suggestions for routine cases
- 📄 **Medical history extraction** — parses an uploaded PDF (labs, medications, allergies, past surgeries) and redacts identifying details the moment it's read
- 📝 **Auto-generated doctor brief** — chief complaint, symptom timeline, relevant history, and 3–5 tailored questions to ask
- ⏰ **Automated follow-up reminders** — scheduled email/SMS check-ins via SendGrid and Twilio
- 🔒 **PII sanitization** — regex-based redaction of phone numbers, emails, national ID formats, and addresses before any text reaches an LLM
- 🛑 **Human-in-the-loop (HITL) safety gate** — any medication dosage language is detected and blocked from reaching the user without doctor review
- 🖥️ **Guided, emergency-aware frontend** — quick-pick symptom chips, live progress through the agent pipeline, and a persistent one-tap emergency-call banner
- 🐳 **Cloud-native deployment** — containerized with a non-root Docker user, deployable to Google Cloud Run out of the box

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | **Google ADK** (Agent Development Kit) |
| LLM | **Gemini 1.5 Flash** |
| Tool / data connectivity | **MCP** (Model Context Protocol) — 4 custom servers |
| Backend API | **FastAPI** + **Pydantic** + **Uvicorn** |
| PDF parsing | **pdfplumber** |
| Location & facility data | **Google Maps Places API** |
| Notifications | **SendGrid** (email), **Twilio** (SMS) |
| Security scanning | **Bandit** |
| Testing | **pytest**, **pytest-asyncio** |
| Frontend | HTML / CSS / vanilla JS |


## Project Structure

```
mediRoute/
├── agents/
│   ├── orchestrator.py       # ADK orchestrator — fans out to sub-agents, applies security gates
│   ├── triage_agent.py       # Classifies symptom urgency (Emergency / Urgent / Routine)
│   ├── document_agent.py     # Extracts + redacts medical history from uploaded PDFs
│   ├── care_finder_agent.py  # Finds and ranks nearby healthcare facilities
│   └── summary_agent.py      # Produces the doctor-visit brief + schedules reminders
├── mcp_servers/
│   ├── medical_kb_server.py  # Symptom-to-condition / red-flag knowledge base
│   ├── pdf_parser_server.py  # PDF text and table extraction
│   ├── places_server.py      # Google Maps Places API wrapper (with mock fallback)
│   └── notifier_server.py    # Email/SMS reminder scheduling
├── security/
│   └── guardrails.py         # PII sanitisation + HITL medication-language gate
├── skills/
│   ├── triage/SKILL.md       # Triage protocol, loaded on demand
│   ├── document/SKILL.md     # Document extraction rules
│   ├── care_finder/SKILL.md  # Care pathway decision rules
│   └── summary/SKILL.md      # Doctor-brief writing guidelines
├── evals/
│   └── test_triage_evals.py  # Triage accuracy evaluation suite
├── tests/
│   └── test_security.py      # PII redaction and HITL gate tests
├── frontend/
│   └── index.html            # Guided intake form + live results UI
├── server.py                 # FastAPI app — /assess, /health, / routes
├── mcp_config.json           # MCP server registry
├── Dockerfile                # Cloud Run deployment image
└── requirements.txt
```

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/mediRoute.git
cd mediRoute

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export GOOGLE_MAPS_API_KEY="your_key_here"      # required for real facility search
export SENDGRID_API_KEY="your_key_here"         # optional — email reminders
export TWILIO_ACCOUNT_SID="your_sid_here"        # optional — SMS reminders
export TWILIO_AUTH_TOKEN="your_token_here"
export TWILIO_FROM_NUMBER="+1234567890"
export SENDER_EMAIL="noreply@yourdomain.com"
```

> All secrets are read from environment variables — nothing is hardcoded. Without `GOOGLE_MAPS_API_KEY` set, the Places server automatically falls back to realistic mock data so the app still runs end-to-end for local demos.

## Requirements

- Python 3.11+
- pip
- (Optional) Docker, for containerized deployment
- (Optional) Google Cloud SDK, for Cloud Run deployment
- API keys: Google Maps Places API, SendGrid, Twilio (all optional except Maps for live facility data)

Full pinned dependencies are listed in [`requirements.txt`](./requirements.txt), covering `google-adk`, `google-generativeai`, `mcp`, `fastapi`, `uvicorn`, `pydantic`, `pdfplumber`, `sendgrid`, `twilio`, `bandit`, and `pytest`.

## Usage

**Run the server locally:**

```bash
python server.py
# Server starts on http://localhost:8080
```

Open `http://localhost:8080` in a browser for the guided intake UI, or call the API directly:

```bash
curl -X POST http://localhost:8080/assess \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Chest tightness and shortness of breath for 2 hours",
    "location": {"lat": 18.5204, "lng": 73.8567},
    "age": 42,
    "user_id": "session_abc123xyz"
  }'
```

**Run tests and security scans:**

```bash
pytest tests/ evals/ -v
bandit -r . --exclude tests/,evals/
```

**Deploy to Cloud Run:**

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/mediroute
gcloud run deploy mediroute \
  --image gcr.io/YOUR_PROJECT/mediroute \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY
```

## Sample Output
<img width="2760" height="1560" alt="mediroute_project_thumbnail" src="https://github.com/user-attachments/assets/3105e500-90aa-4e68-9cfb-7c70589a6580" />

Request:
```json
{
  "symptoms": "Chest tightness and shortness of breath for 2 hours",
  "location": { "lat": 18.5204, "lng": 73.8567 },
  "age": 42,
  "user_id": "session_abc123xyz"
}
```

Response (abridged):
```json
{
  "urgency": "URGENT",
  "hitl_required": false,
  "response": {
    "triage": {
      "urgency": "URGENT",
      "flag_reason": "Chest tightness and shortness of breath — seek care within a few hours."
    },
    "care_finder": {
      "facilities": [
        { "name": "Ruby Hall Clinic — urgent care", "distance_km": 1.8, "wait_time_mins": 15 },
        { "name": "Sahyadri Hospital — ER", "distance_km": 3.2, "wait_time_mins": 30 }
      ]
    },
    "summary": {
      "doctor_brief": {
        "chief_complaint": "Chest tightness and breathlessness for 2 hours.",
        "questions_to_ask": [
          "Should I get an ECG today?",
          "Any exertion or stress trigger to note?"
        ]
      },
      "reminders": [
        { "type": "follow_up", "message": "Check in on symptoms", "send_at": "tomorrow, 9:00 AM" }
      ]
    }
  }
}
```

## Workflow

```
User input (symptoms + location + optional PDF)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  Security boundary — PII sanitisation                   │
│                                                         │
│              ┌─────────────────────────┐                │
│              │  Orchestrator Agent (ADK) │              │
│              └──┬──────┬────────┬───────┘               │
│                 │      │        │                       │
│           Triage   Document  Care Finder  →  Summary    │
│           agent    agent     agent           agent      │
│              │        │          │              │       │
│         Medical    PDF Parser  Places API    Notifier   │
│          KB MCP       MCP        MCP           MCP      │
│                                                         │
│  Security boundary — HITL medication-language gate      │
└─────────────────────────────────────────────────────────┘
        │
        ▼
  Structured JSON → rendered as urgency banner, care list,
  doctor brief, and reminders in the frontend
```

1. **Sanitise** — strip PII from the raw request before any agent sees it.
2. **Triage** — classify urgency, always escalating when uncertain.
3. **Parse document** (if provided) — extract and redact medical history in parallel with triage.
4. **Find care** — rank nearby facilities using the urgency level + location.
5. **Summarise** — generate the doctor brief and schedule reminders.
6. **HITL gate** — scan the combined output for medication-dosage language and block anything unapproved.
7. **Respond** — return a single structured payload the frontend renders as urgency banner, care options, brief, and reminders.

## Challenges Faced

- **Keeping safety deterministic, not just prompted.** Relying on an LLM's system prompt alone to never suggest medication dosages isn't a strong enough guarantee — the `hitl_gate()` regex layer exists specifically as a hard, code-level backstop independent of model behavior.
- **Coordinating agent order and dependencies.** The summary agent needs both triage and document output before it can run, while care-finder only needs triage — required carefully sequencing/parallelizing sub-agent calls in the orchestrator rather than firing everything at once.
- **Designing for demo reliability without real API keys.** Google Maps, SendGrid, and Twilio all require paid/verified accounts, so the Places server needed a realistic mock-data fallback to keep the whole pipeline demoable end-to-end offline.
- **Balancing PII redaction recall vs. precision.** Regex-based redaction (Aadhaar, PAN, phone, email, address patterns) is fast and auditable but not foolproof — tuning patterns to catch real PII without over-redacting legitimate symptom descriptions took iteration.
- **Managing prompt size across four agents.** Each sub-agent has a narrow, strict JSON-only output contract — the `skills/*/SKILL.md` progressive-disclosure pattern keeps each agent's context focused instead of one bloated shared prompt.

## Future Improvements

- Replace regex-based PII/HITL detection with a dedicated PII/PHI detection model for higher recall
- Build an actual doctor-review dashboard so flagged HITL content is queued for real human approval instead of just redacted
- Persist reminders and session history in a real database instead of in-memory storage
- Add user authentication and multi-session history instead of ephemeral session tokens
- Stream live agent progress to the frontend via WebSockets instead of a simulated pipeline animation
- Support multilingual symptom input for broader accessibility
- Add a feedback loop to calibrate triage confidence against real outcomes over time
- Expand the medical knowledge base beyond the current symptom set, ideally backed by a licensed ontology (e.g. SNOMED CT)
- Add CI/CD (lint, test, security scan, deploy) on every push

## Learning Outcomes

- Designing and orchestrating a **multi-agent system** with Google ADK, including sub-agent sequencing and dependency management
- Building and registering custom **MCP servers** to give agents structured tool access to external data (maps, PDFs, notifications, a knowledge base)
- Writing **strict, schema-constrained prompts** so each agent reliably returns parseable JSON
- Implementing real **AI safety guardrails** — PII sanitisation and a human-in-the-loop gate — as deterministic code, not just prompt instructions
- Shipping a full **FastAPI backend** with validation, error handling, and a Cloud Run–ready Docker deployment
- Building an **agent-aware frontend** that reflects a multi-step backend pipeline back to the user in an understandable way
- Writing **evals and security tests** specifically for an AI system's behavior, not just its code paths

## Author

**Prachi Barve**

---

⚠️ **Disclaimer:** MediRoute is a navigation and triage aid. It does **not** provide medical diagnoses or prescriptions. Always consult a qualified healthcare professional for medical advice. In an emergency, call your local emergency services immediately.
