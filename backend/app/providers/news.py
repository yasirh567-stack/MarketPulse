"""News providers: public RSS (Google News, no API key) and demo fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.sanitize import clean_text, safe_url
from app.providers.base import RawArticle
from app.providers.demo_data import get_demo_news_articles, is_demo_ticker
from app.schemas.common import DataStatus

logger = get_logger("app.providers.news")

GOOGLE_NEWS_RSS_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


class DemoNewsProvider:
    name = "demo"

    def get_headlines(self, ticker: str, limit: int) -> list[RawArticle]:
        articles = get_demo_news_articles(ticker)
        return [
            RawArticle(
                ticker=ticker.upper(),
                title=clean_text(a["title"]),
                summary=clean_text(a["summary"]),
                url=a["url"],
                source=a["source"],
                published_at=a["published_at"],
                data_status=DataStatus.DEMO,
                is_demo=True,
            )
            for a in sorted(articles, key=lambda a: a["published_at"], reverse=True)[:limit]
        ]


class RssNewsProvider:
    """Free financial headlines via Google News' public RSS search endpoint.

    No API key is required. This is explicitly a *free-tier fallback*, not an
    official financial newswire — headlines are labeled "cached" once stored,
    reflecting that RSS delivery timing is not guaranteed to be immediate.
    """

    name = "rss"

    def get_headlines(self, ticker: str, limit: int) -> list[RawArticle]:
        import feedparser
        import httpx

        query = f"{ticker} stock"
        url = GOOGLE_NEWS_RSS_TEMPLATE.format(query=quote(query))
        response = httpx.get(url, timeout=8.0, follow_redirects=True)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)

        articles: list[RawArticle] = []
        for entry in parsed.entries[:limit]:
            link = safe_url(entry.get("link"))
            if not link:
                continue
            published_struct = entry.get("published_parsed")
            published_at = (
                datetime(*published_struct[:6], tzinfo=UTC)
                if published_struct
                else datetime.now(UTC)
            )
            source_title = (
                entry.get("source", {}).get("title") if entry.get("source") else "Google News"
            )
            articles.append(
                RawArticle(
                    ticker=ticker.upper(),
                    title=clean_text(entry.get("title", "")),
                    summary=clean_text(entry.get("summary", "")),
                    url=link,
                    source=source_title or "Google News",
                    published_at=published_at,
                    data_status=DataStatus.CACHED,
                    is_demo=False,
                )
            )
        return articles


class CompositeNewsProvider:
    def __init__(self, settings: Settings, live: RssNewsProvider | None = None):
        self.settings = settings
        self.live = live if live is not None else RssNewsProvider()
        self.demo = DemoNewsProvider()

    def get_headlines(self, ticker: str, limit: int = 20) -> list[RawArticle]:
        # See the analogous fix/comment in app.providers.market.CompositeMarketDataProvider
        # — bundled demo tickers must still be attempted live when DEMO_MODE=false.
        if not self.settings.demo_mode:
            try:
                articles = self.live.get_headlines(ticker, limit)
                if articles:
                    return articles
            except Exception as exc:
                logger.warning("Live news fetch failed for %s: %s", ticker, exc)
        if is_demo_ticker(ticker):
            return self.demo.get_headlines(ticker, limit)
        return []
