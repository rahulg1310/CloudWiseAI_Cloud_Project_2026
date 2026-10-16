import logging
import time
from collections import defaultdict, deque
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import config
from app.common import latest_date
from app.database import db_session
from app.routers import anomalies, costs, predictions, recommendations, utilization
from app.security import get_token_user_id
from app.services import assistant as assistant_service

log = logging.getLogger("cloudwise.assistant")

router = APIRouter(prefix="/assistant", tags=["assistant"])

# Every message costs money, so cap how fast one user can send them.
# In-memory, so it is per server process (fine for a single uvicorn worker).
RATE_LIMIT_MESSAGES = 15
RATE_LIMIT_WINDOW_SECONDS = 60
_recent_requests = defaultdict(deque)


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=assistant_service.MAX_MESSAGE_CHARS)
    history: list[HistoryItem] = Field(default_factory=list, max_length=30)


def check_rate_limit(user_id):
    now = time.monotonic()
    recent = _recent_requests[user_id]
    while recent and now - recent[0] > RATE_LIMIT_WINDOW_SECONDS:
        recent.popleft()
    if len(recent) >= RATE_LIMIT_MESSAGES:
        raise HTTPException(status_code=429, detail="You're sending messages too quickly. Wait a moment and try again.")
    recent.append(now)


def gather_data(conn):
    """Collect everything the assistant may talk about, reusing the endpoint functions."""
    with conn.cursor() as cur:
        latest = latest_date(cur)
        if latest is None:
            return None

        cur.execute(
            """SELECT billing_period, service, SUM(cost) AS cost FROM cost_records
               WHERE billing_period IN (SELECT DISTINCT billing_period FROM cost_records
                                        ORDER BY billing_period DESC LIMIT 3)
               GROUP BY billing_period, service ORDER BY billing_period DESC, cost DESC"""
        )
        monthly = {}
        for r in cur.fetchall():
            monthly.setdefault(r["billing_period"], []).append((r["service"], float(r["cost"])))

        cur.execute(
            """SELECT resource_id, service, region, SUM(cost) AS cost FROM cost_records
               WHERE date > %s GROUP BY resource_id, service, region ORDER BY cost DESC LIMIT 8""",
            (latest - timedelta(days=30),),
        )
        top_resources = [dict(r, cost=float(r["cost"])) for r in cur.fetchall()]

    return {
        "as_of": latest.isoformat(),
        "period": latest.strftime("%Y-%m"),
        "summary": costs.summary(conn=conn),
        "breakdown": costs.breakdown(conn=conn),
        "trend": costs.trend(days=14, conn=conn),
        "anomalies": anomalies.list_anomalies(limit=50, conn=conn),
        "recommendations": recommendations.list_recommendations(conn=conn),
        "utilization": utilization.utilization(conn=conn),
        "predictions": predictions.predictions(conn=conn),
        "monthly_by_service": monthly,
        "top_resources": top_resources,
    }


@router.post("/chat")
def chat(body: ChatRequest, user_id: int = Depends(get_token_user_id)):
    if not config.llm_is_configured():
        raise HTTPException(
            status_code=503,
            detail="The assistant isn't set up yet. Add LLM_API_KEY to the backend .env file and restart the server.",
        )
    check_rate_limit(user_id)

    # Short database session: released before the (slow) LLM call.
    with db_session() as conn:
        data = gather_data(conn)

    system = assistant_service.SYSTEM_PROMPT + "\n\n" + assistant_service.format_context(data)
    messages = assistant_service.build_messages([h.model_dump() for h in body.history], body.message)

    try:
        reply = assistant_service.ask_llm(system, messages)
    except assistant_service.LLMError as error:
        log.error("LLM call failed: %s", error)
        raise HTTPException(status_code=502, detail=error.user_hint or "The AI service didn't respond. Please try again in a moment.")

    return {"reply": reply}
