"""Optional social-media provider (Reddit). Disabled by default.

The rest of the app treats an empty post list exactly the same as "social
provider disabled" — sentiment aggregation simply has zero social rows and
falls back entirely to news sentiment. Nothing breaks in its absence.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.providers.base import RawSocialPost

logger = get_logger("app.providers.social")


class RedditSocialProvider:
    """Uses PRAW-style OAuth if `ENABLE_REDDIT=true` and credentials are set.

    Implemented as an HTTP call to Reddit's free OAuth API rather than adding
    a PRAW dependency, since only simple read-only search is needed here.
    """

    name = "reddit"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = bool(
            settings.enable_reddit and settings.reddit_client_id and settings.reddit_client_secret
        )
        self._token: str | None = None

    def _get_token(self) -> str | None:
        import httpx

        if self._token:
            return self._token
        if not self.settings.reddit_client_id or not self.settings.reddit_client_secret:
            return None
        try:
            resp = httpx.post(
                "https://www.reddit.com/api/v1/access_token",
                data={"grant_type": "client_credentials"},
                auth=(self.settings.reddit_client_id, self.settings.reddit_client_secret),
                headers={"User-Agent": self.settings.reddit_user_agent},
                timeout=8.0,
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token
        except Exception as exc:
            logger.warning("Reddit auth failed: %s", exc)
            return None

    def get_posts(self, ticker: str, limit: int = 20) -> list[RawSocialPost]:
        if not self.enabled:
            return []
        from datetime import UTC, datetime

        import httpx

        from app.core.sanitize import clean_text, safe_url

        token = self._get_token()
        if not token:
            return []
        try:
            resp = httpx.get(
                "https://oauth.reddit.com/search",
                params={"q": ticker, "sort": "new", "limit": limit},
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": self.settings.reddit_user_agent,
                },
                timeout=8.0,
            )
            resp.raise_for_status()
            children = resp.json().get("data", {}).get("children", [])
        except Exception as exc:
            logger.warning("Reddit search failed for %s: %s", ticker, exc)
            return []

        posts = []
        for child in children:
            data = child.get("data", {})
            posts.append(
                RawSocialPost(
                    ticker=ticker.upper(),
                    platform="reddit",
                    external_id=str(data.get("id")),
                    text=clean_text(f"{data.get('title', '')}. {data.get('selftext', '')}"),
                    author=data.get("author"),
                    url=safe_url(f"https://reddit.com{data.get('permalink', '')}"),
                    created_at=datetime.fromtimestamp(data.get("created_utc", 0), tz=UTC),
                    is_demo=False,
                )
            )
        return posts


class NullSocialProvider:
    """Used whenever Reddit is disabled/unconfigured — a no-op that keeps the
    interface uniform for callers."""

    name = "none"
    enabled = False

    def get_posts(self, ticker: str, limit: int) -> list[RawSocialPost]:
        return []


def get_social_provider(settings: Settings):
    if settings.enable_reddit:
        provider = RedditSocialProvider(settings)
        if provider.enabled:
            return provider
    return NullSocialProvider()
