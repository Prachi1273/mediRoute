"""
MediRoute FastAPI Server
------------------------
REST API that wraps the orchestrator agent.
Deployed to Google Cloud Run (Day 1 + Day 5 deployability concept).

Endpoints:
  POST /assess     — main health assessment
  GET  /health     — health check for Cloud Run
  GET  /           — simple landing page
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from agents.orchestrator import run_mediRoute
from security.guardrails import validate_location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mediRoute.server")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class LocationModel(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class AssessmentRequest(BaseModel):
    symptoms: str = Field(..., min_length=5, max_length=2000)
    location: LocationModel
    pdf_path: str | None = None
    age: int | None = Field(None, ge=0, le=120)
    user_id: str = Field(..., min_length=8, max_length=64)  # session token only


class AssessmentResponse(BaseModel):
    urgency: str
    response: dict
    hitl_required: bool
    session_id: str


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MediRoute server starting up")
    yield
    logger.info("MediRoute server shutting down")


app = FastAPI(
    title="MediRoute",
    description="AI-powered health navigation agent",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html><body style="font-family:sans-serif;padding:2rem">
    <h1>🏥 MediRoute</h1>
    <p>AI-powered health navigation agent.</p>
    <p><a href="/docs">API docs →</a></p>
    </body></html>
    """


@app.get("/health")
async def health_check():
    """Cloud Run health probe."""
    return {"status": "ok", "service": "mediRoute"}


@app.post("/assess", response_model=AssessmentResponse)
async def assess(request: AssessmentRequest):
    """
    Main health assessment endpoint.
    Accepts symptoms + location, returns urgency level, care options,
    and a doctor-visit brief.
    """
    if not validate_location(request.location.model_dump()):
        raise HTTPException(status_code=400, detail="Invalid location coordinates")

    try:
        result = await run_mediRoute({
            "symptoms": request.symptoms,
            "location": request.location.model_dump(),
            "pdf_path": request.pdf_path,
            "age": request.age,
            "user_id": request.user_id,
        })
    except Exception as e:
        logger.error("Agent error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Agent processing failed")

    response_data = result.get("response", {})
    urgency = "UNKNOWN"
    if isinstance(response_data, dict):
        urgency = response_data.get("triage", {}).get("urgency", "UNKNOWN")

    return AssessmentResponse(
        urgency=urgency,
        response=result,
        hitl_required=result.get("hitl_required", False),
        session_id=request.user_id,
    )


# ---------------------------------------------------------------------------
# Cloud Run entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="info")
