"""Application configuration, sourced from environment variables / .env.

Centralizing settings here means every other module imports `get_settings()`
instead of reading `os.environ` directly, keeping secrets and toggles in one
auditable place.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core mode ---
    demo_mode: bool = True
    environment: str = "development"
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "sqlite:///./marketpulse.db"

    # --- Cache ---
    redis_url: str | None = None
    cache_default_ttl_seconds: int = 300

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Providers ---
    market_data_provider: str = "yfinance"
    news_provider: str = "rss"
    enable_reddit: bool = False
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "marketpulse-ai/0.1"
    enable_finbert: bool = False

    # Optional: Federal Reserve Economic Data (FRED) API, used for the
    # Buffett Indicator (market-cap-to-GDP) macro widget. Free to register at
    # https://fred.stlouisfed.org/docs/api/api_key.html. Off by default —
    # falls back to a clearly-labeled demo series when disabled/unavailable.
    enable_fred: bool = False
    fred_api_key: str | None = None

    # --- WebSocket ---
    market_poll_interval_seconds: float = 15.0

    # --- Rate limiting ---
    rate_limit_per_minute: int = 120

    # --- Demo tickers bundled in data/demo ---
    demo_tickers: str = "AAPL,MSFT,TSLA,NVDA,GME,CHTR"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def demo_ticker_list(self) -> list[str]:
        return [t.strip().upper() for t in self.demo_tickers.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — safe because env vars don't change at runtime."""
    return Settings()
