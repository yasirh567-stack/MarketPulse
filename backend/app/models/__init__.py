"""SQLAlchemy ORM models.

Importing this package registers all model classes on `Base.metadata`, which
Alembic's `env.py` relies on for autogeneration.
"""

from app.models.backtest import BacktestRun
from app.models.cache import CacheEntry
from app.models.event import DetectedEvent
from app.models.instrument import Instrument
from app.models.market_data import PriceBar, PriceSnapshot
from app.models.ml import ModelRun, Prediction
from app.models.news import NewsArticle, SocialPost
from app.models.provider_health import ProviderHealth
from app.models.sentiment import SentimentScore
from app.models.watchlist import Watchlist, WatchlistItem

__all__ = [
    "BacktestRun",
    "CacheEntry",
    "DetectedEvent",
    "Instrument",
    "PriceBar",
    "PriceSnapshot",
    "ModelRun",
    "Prediction",
    "NewsArticle",
    "SocialPost",
    "ProviderHealth",
    "SentimentScore",
    "Watchlist",
    "WatchlistItem",
]
