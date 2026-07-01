# 🏥 MediRoute — AI Health Navigation Agent

> **Kaggle Capstone — Agents for Good track**  
> Built for the 5-Day AI Agents: Intensive Vibe Coding Course with Google

MediRoute is a multi-agent AI system that helps people navigate the healthcare system when they feel unwell. It takes a user's symptoms, location, and optional medical history PDF, then returns:

- **Urgency classification** (Emergency / Urgent / Routine)
- **Nearby care options** (ER, urgent care, GP, telehealth)
- **Doctor-visit brief** — a structured summary to show your doctor
- **Follow-up reminders** — appointment and medication reminders via email/SMS

---

## Architecture

```
User input (symptoms + location + optional PDF)
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Security boundary (PII sanitisation + HITL gate)   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │         Orchestrator Agent (ADK)             │   │
│  └────┬──────────┬──────────┬──────────┬────────┘   │
│       │          │          │          │             │
│  Triage    Doc parser  Care finder  Summary         │
│  agent      agent       agent        agent          │
│    │           │           │            │           │
│  Medical    PDF        Places API   Notifier        │
│  KB MCP    Parser MCP  MCP          MCP             │
└─────────────────────────────────────────────────────┘
        │
        ▼ (passes HITL gate)
  Structured response to user
```

## Course concepts demonstrated

| Concept | Where |
|---------|-------|
| Multi-agent system (ADK) | `agents/orchestrator.py` + 4 sub-agents |
| MCP servers | `mcp_servers/` (4 custom servers) |
| Antigravity | Built and demoed in Antigravity IDE |
| Security features | `security/guardrails.py` — PII redaction + HITL gate |
| Deployability | `Dockerfile` + Cloud Run config |
| Agent skills | `skills/*/SKILL.md` — progressive disclosure pattern |

---

## Project structure

```
mediRoute/
├── agents/
│   ├── orchestrator.py       # ADK orchestrator — fans out to sub-agents
│   ├── triage_agent.py       # Classifies symptom urgency
│   ├── document_agent.py     # Extracts medical history from PDFs
│   ├── care_finder_agent.py  # Finds nearby healthcare facilities
│   └── summary_agent.py      # Produces doctor-visit brief + reminders
├── mcp_servers/
│   ├── medical_kb_server.py  # Symptom-to-condition knowledge base
│   ├── pdf_parser_server.py  # PDF text/table extraction
│   ├── places_server.py      # Google Maps Places API wrapper
│   └── notifier_server.py    # Email/SMS reminders (SendGrid + Twilio)
├── security/
│   └── guardrails.py         # PII sanitisation + HITL medication gate
├── skills/
│   ├── triage/SKILL.md       # Triage protocol (loaded on demand)
│   ├── document/SKILL.md     # Document extraction rules
│   ├── care_finder/SKILL.md  # Care pathway decision rules
│   └── summary/SKILL.md      # Doctor brief writing guidelines
├── evals/
│   └── test_triage_evals.py  # Triage accuracy evaluation suite
├── tests/
│   └── test_security.py      # PII and HITL security tests
├── server.py                 # FastAPI server for Cloud Run
├── mcp_config.json           # MCP server registry for Antigravity
├── Dockerfile                # Cloud Run deployment
└── requirements.txt
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/mediRoute
cd mediRoute
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export GOOGLE_MAPS_API_KEY="your_key_here"       # Required for care finder
export SENDGRID_API_KEY="your_key_here"           # Optional — email reminders
export TWILIO_ACCOUNT_SID="your_sid_here"         # Optional — SMS reminders
export TWILIO_AUTH_TOKEN="your_token_here"
export TWILIO_FROM_NUMBER="+1234567890"
export SENDER_EMAIL="noreply@yourdomain.com"
```

> **Note:** All keys are read from environment variables. Never commit API keys to git.

### 3. Run locally

```bash
python server.py
# Server starts on http://localhost:8080
```

### 4. Run in Antigravity

Open `mcp_config.json` in Antigravity — the MCP servers are auto-detected
and registered. Then vibe-code improvements directly in the IDE.

```bash
# Install agents-cli (Day 3 concept)
npm install -g @google/agents-cli

# Scaffold, lint, test
agents lint agents/
agents test evals/
```

### 5. Run tests

```bash
pytest tests/ evals/ -v

# Security scan (Day 4 concept)
bandit -r . --exclude tests/,evals/
```

---

## Deploy to Cloud Run

```bash
# Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT/mediRoute

# Deploy
gcloud run deploy mediRoute \
  --image gcr.io/YOUR_PROJECT/mediRoute \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY
```

---

## API usage

```bash
curl -X POST https://your-cloud-run-url/assess \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Chest tightness and shortness of breath for 2 hours",
    "location": {"lat": 18.5204, "lng": 73.8567},
    "age": 42,
    "user_id": "session_abc123xyz"
  }'
```

---

## Security design

1. **PII sanitisation** — Aadhaar, PAN, phone, email, address are redacted before any agent sees the input
2. **HITL gate** — Any medication dosage language is flagged and blocked from reaching the user without doctor review
3. **No API keys in code** — All secrets via environment variables
4. **Non-root container** — Dockerfile runs as a dedicated `mediRoute` user
5. **Input validation** — Location coordinates validated, symptoms length bounded, user_id is a session token (not a real name)

---

## Disclaimer

MediRoute is a navigation and triage aid. It does **not** provide medical diagnoses or prescriptions. Always consult a qualified healthcare professional for medical advice. In an emergency, call your local emergency services immediately.
