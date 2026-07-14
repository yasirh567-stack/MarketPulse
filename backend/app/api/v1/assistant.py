# NOTE: intentionally no `from __future__ import annotations` — see the
# comment in app/api/v1/backtests.py; slowapi's @limiter.limit decorator
# breaks FastAPI's param resolution under postponed annotation evaluation.

from fastapi import APIRouter, Request

from app.api.deps import AppSettings, DbSession
from app.core.rate_limit import default_rate_limit, limiter
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.services.assistant import answer_question

router = APIRouter()


@router.post("/query", response_model=AssistantQueryResponse)
@limiter.limit(default_rate_limit())
def query_assistant(
    request: Request, body: AssistantQueryRequest, db: DbSession, settings: AppSettings
):
    result = answer_question(db, settings, body.ticker.upper(), body.question)
    return AssistantQueryResponse(
        ticker=result.ticker,
        question=result.question,
        answer=result.answer,
        citations=result.citations,
        disclaimer=result.disclaimer,
        data_sufficient=result.data_sufficient,
    )
