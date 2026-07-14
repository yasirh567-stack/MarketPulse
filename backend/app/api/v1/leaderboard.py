# NOTE: intentionally no `from __future__ import annotations` — see the
# comment in app/api/v1/backtests.py; slowapi's @limiter.limit decorator
# breaks FastAPI's param resolution under postponed annotation evaluation.

from fastapi import APIRouter, Query, Request

from app.api.deps import AppSettings, DbSession
from app.core.rate_limit import default_rate_limit, limiter
from app.schemas.leaderboard import LeaderboardResponse
from app.services.leaderboard_service import get_leaderboard

router = APIRouter()


@router.get("", response_model=LeaderboardResponse)
@limiter.limit(default_rate_limit())
def get_leaderboard_endpoint(
    request: Request,
    db: DbSession,
    settings: AppSettings,
    tickers: str | None = Query(
        None, description="Comma-separated tickers. Defaults to the bundled demo tickers."
    ),
    model_name: str = Query("gradient_boosting"),
):
    """Compares model quality across several tickers in one call — a stale
    (>12h old) or missing model for any ticker is trained on demand via the
    same `get_or_train` path `/predictions/{ticker}` uses, so a fully-cold
    call can take several seconds per stale ticker."""
    ticker_list = (
        [t.strip().upper() for t in tickers.split(",") if t.strip()]
        if tickers
        else settings.demo_ticker_list
    )
    entries = get_leaderboard(db, settings, ticker_list[:25], model_name)
    return LeaderboardResponse(entries=entries)
