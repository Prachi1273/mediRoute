"""
Notifier — MCP Server
----------------------
Schedules and sends follow-up reminders via email and SMS.
Uses SendGrid for email and Twilio for SMS.

Both API keys are read from environment variables — NEVER hardcoded.
Day 4 security concept: no secrets in code.
"""

import os
import json
import logging
from datetime import datetime
from mcp.server import MCPServer

logger = logging.getLogger("mediRoute.notifier")

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.environ.get("TWILIO_FROM_NUMBER", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@mediRoute.app")

app = MCPServer(name="notifier", version="1.0.0")

# In-memory store for demo — replace with a DB in production
_scheduled_reminders: list[dict] = []


@app.tool(
    name="schedule_reminder",
    description="Schedule a follow-up reminder to be sent at a specific time.",
    input_schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "message": {"type": "string"},
            "send_at": {"type": "string", "description": "ISO 8601 datetime string"},
            "channel": {"type": "string", "enum": ["email", "sms", "both"], "default": "email"},
        },
        "required": ["session_id", "message", "send_at"],
    },
)
def schedule_reminder(session_id: str, message: str, send_at: str, channel: str = "email") -> dict:
    """Store a reminder for later delivery."""
    reminder = {
        "session_id": session_id,
        "message": message,
        "send_at": send_at,
        "channel": channel,
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
    }
    _scheduled_reminders.append(reminder)
    logger.info("Reminder scheduled for session %s at %s", session_id, send_at)
    return {"status": "scheduled", "reminder_id": len(_scheduled_reminders) - 1}


@app.tool(
    name="send_email",
    description="Send an immediate email notification to the user.",
    input_schema={
        "type": "object",
        "properties": {
            "to_email": {"type": "string", "description": "Recipient email (already validated)"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["to_email", "subject", "body"],
    },
)
def send_email(to_email: str, subject: str, body: str) -> dict:
    """Send an email via SendGrid (or log in demo mode)."""
    if not SENDGRID_API_KEY:
        logger.info("[DEMO] Email to %s | Subject: %s | Body: %s", to_email, subject, body[:80])
        return {"status": "demo_sent", "to": to_email}

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        mail = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )
        response = sg.client.mail.send.post(request_body=mail.get())
        return {"status": "sent", "status_code": response.status_code}
    except Exception as e:
        logger.error("Email failed: %s", e)
        return {"status": "error", "error": str(e)}


@app.tool(
    name="send_sms",
    description="Send an immediate SMS notification to the user.",
    input_schema={
        "type": "object",
        "properties": {
            "to_number": {"type": "string", "description": "E.164 formatted phone number"},
            "message": {"type": "string", "description": "SMS body (max 160 chars recommended)"},
        },
        "required": ["to_number", "message"],
    },
)
def send_sms(to_number: str, message: str) -> dict:
    """Send an SMS via Twilio (or log in demo mode)."""
    if not TWILIO_SID:
        logger.info("[DEMO] SMS to %s | Message: %s", to_number, message[:80])
        return {"status": "demo_sent", "to": to_number}

    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            body=message[:160],
            from_=TWILIO_FROM,
            to=to_number,
        )
        return {"status": "sent", "sid": msg.sid}
    except Exception as e:
        logger.error("SMS failed: %s", e)
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    app.run(transport="stdio")
