"""Macro market-valuation indicators — currently just the "Buffett Indicator"
(total US stock market value ÷ GDP), the market-cap-to-GDP heuristic Warren
Buffett has cited as "probably the best single measure of where valuations
stand at any given moment."

This is a market-wide gauge, not a per-ticker prediction, and it is presented
strictly as historical/contextual information — a high or low reading is
never translated into a buy/sell recommendation anywhere in this app.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.core.config import Settings
from app.core.logging import get_logger
from app.providers.demo_data import DEMO_DIR
from app.schemas.common import DataStatus

logger = get_logger("app.providers.macro")

# Standard free-data proxy for the Buffett Indicator, used by most DIY
# trackers: Wilshire 5000 Full Cap Price Index (approximates total US market
# capitalization) divided by nominal GDP. Both series are published free by
# the Federal Reserve (FRED). This is an approximation, not an official
# "total market cap" figure — disclosed in the API response's methodology_note.
FRED_WILSHIRE_SERIES_ID = "WILL5000INDFC"
FRED_GDP_SERIES_ID = "GDP"
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


@dataclass
class QuarterlyRatio:
    quarter_end: date
    ratio_pct: float


@dataclass
class BuffettIndicatorData:
    current_ratio_pct: float
    as_of: datetime
    historical: list[QuarterlyRatio]
    data_status: DataStatus
    source: str


class DemoBuffettIndicatorProvider:
    name = "demo"

    def get(self) -> BuffettIndicatorData:
        import json

        path = DEMO_DIR / "macro" / "buffett_indicator.json"
        payload = json.loads(path.read_text())
        now = datetime.now(UTC)
        historical = []
        for obs in payload["quarterly_observations"]:
            # Resolve quarters-ago -> an approximate quarter-end date, same
            # "offset, not baked-in date" pattern as the price/news fixtures.
            quarter_end = (now - timedelta(days=obs["quarters_ago"] * 91)).date()
            historical.append(QuarterlyRatio(quarter_end=quarter_end, ratio_pct=obs["ratio_pct"]))
        historical.sort(key=lambda r: r.quarter_end)
        return BuffettIndicatorData(
            current_ratio_pct=historical[-1].ratio_pct,
            as_of=now,
            historical=historical,
            data_status=DataStatus.DEMO,
            source=self.name,
        )


class FredBuffettIndicatorProvider:
    """Real implementation using the Federal Reserve's free FRED API.

    Requires a free API key (ENABLE_FRED=true + FRED_API_KEY) — see
    docs/data-sources.md for registration instructions. Any failure (missing
    key, network error, unexpected response shape) raises, letting the
    composite provider fall back to the demo series.
    """

    name = "fred"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _fetch_series(self, series_id: str) -> list[tuple[date, float]]:
        import httpx

        response = httpx.get(
            FRED_BASE_URL,
            params={
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "asc",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        observations = response.json()["observations"]
        out = []
        for obs in observations:
            if obs["value"] == ".":
                continue  # FRED's marker for "not yet published"
            out.append((date.fromisoformat(obs["date"]), float(obs["value"])))
        return out

    def get(self) -> BuffettIndicatorData:
        wilshire = self._fetch_series(FRED_WILSHIRE_SERIES_ID)
        gdp = self._fetch_series(FRED_GDP_SERIES_ID)
        if not wilshire or not gdp:
            raise ValueError("FRED returned no observations for Wilshire 5000 or GDP")

        # Align each GDP quarter to the closest Wilshire observation on or
        # before that quarter's date, giving one ratio point per quarter.
        historical: list[QuarterlyRatio] = []
        wilshire_idx = 0
        for gdp_date, gdp_value in gdp:
            while wilshire_idx + 1 < len(wilshire) and wilshire[wilshire_idx + 1][0] <= gdp_date:
                wilshire_idx += 1
            if wilshire[wilshire_idx][0] > gdp_date:
                continue  # no Wilshire data yet as of this early GDP point
            wilshire_value = wilshire[wilshire_idx][1]
            ratio_pct = (wilshire_value / gdp_value) * 100
            historical.append(QuarterlyRatio(quarter_end=gdp_date, ratio_pct=round(ratio_pct, 2)))

        latest_wilshire_date, latest_wilshire_value = wilshire[-1]
        latest_gdp_value = gdp[-1][1]
        current_ratio_pct = round((latest_wilshire_value / latest_gdp_value) * 100, 2)

        return BuffettIndicatorData(
            current_ratio_pct=current_ratio_pct,
            as_of=datetime.combine(latest_wilshire_date, datetime.min.time(), tzinfo=UTC),
            historical=historical,
            data_status=DataStatus.CACHED,
            source=self.name,
        )


class CompositeBuffettIndicatorProvider:
    def __init__(self, settings: Settings, live: FredBuffettIndicatorProvider | None = None):
        self.settings = settings
        self.demo = DemoBuffettIndicatorProvider()
        if live is not None:
            self.live: FredBuffettIndicatorProvider | None = live
        elif settings.enable_fred and settings.fred_api_key:
            self.live = FredBuffettIndicatorProvider(settings.fred_api_key)
        else:
            self.live = None

    def get(self) -> BuffettIndicatorData:
        if not self.settings.demo_mode and self.live is not None:
            try:
                return self.live.get()
            except Exception as exc:
                logger.warning("FRED Buffett Indicator fetch failed, using demo: %s", exc)
        return self.demo.get()
