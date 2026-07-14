"""Loads bundled demo fixtures (data/demo/) and resolves their relative
offsets (trading-days-ago / hours-ago) into real timestamps at request time.

See scripts/generate_demo_fixtures.py for how these fixtures are produced —
fixtures store offsets rather than absolute dates specifically so demo mode
keeps looking "current" no matter when someone runs the project.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_DIR = REPO_ROOT / "data" / "demo"


def _resolve_trading_date(offset_trading_days: int, now: datetime) -> datetime:
    """Step backward `offset_trading_days` weekdays from `now`, landing on a
    weekday close (used as each synthetic bar's timestamp)."""
    d = now
    remaining = offset_trading_days
    while remaining > 0:
        d -= timedelta(days=1)
        if d.weekday() < 5:  # Mon-Fri
            remaining -= 1
    # normalize to a consistent "market close" time of day
    return d.replace(hour=20, minute=0, second=0, microsecond=0)


@lru_cache(maxsize=32)
def _load_price_fixture(ticker: str) -> dict | None:
    path = DEMO_DIR / "prices" / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


@lru_cache(maxsize=32)
def _load_news_fixture(ticker: str) -> dict | None:
    path = DEMO_DIR / "news" / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def load_instruments_manifest() -> list[dict]:
    path = DEMO_DIR / "instruments.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def get_demo_price_bars(ticker: str, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(UTC)
    fixture = _load_price_fixture(ticker)
    if fixture is None:
        return []
    bars = []
    for bar in fixture["bars"]:
        ts = _resolve_trading_date(bar["offset_trading_days"], now)
        bars.append({**bar, "ts": ts})
    return bars


def get_demo_news_articles(ticker: str, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(UTC)
    fixture = _load_news_fixture(ticker)
    if fixture is None:
        return []
    articles = []
    for art in fixture["articles"]:
        published_at = now - timedelta(hours=art["hours_ago"])
        articles.append({**art, "published_at": published_at})
    return articles


def is_demo_ticker(ticker: str) -> bool:
    return _load_price_fixture(ticker) is not None
