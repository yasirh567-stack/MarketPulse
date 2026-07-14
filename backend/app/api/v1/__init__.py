from fastapi import APIRouter

from app.api.v1 import (
    assistant,
    backtests,
    events,
    health,
    instruments,
    leaderboard,
    macro,
    market,
    news,
    predictions,
    sentiment,
    watchlists,
    ws,
)
from app.api.v1 import (
    models as models_router,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(instruments.router, prefix="/instruments", tags=["instruments"])
api_router.include_router(macro.router, prefix="/macro", tags=["macro"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(models_router.router, prefix="/models", tags=["models"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(ws.router, tags=["websocket"])
