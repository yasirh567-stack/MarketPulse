from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import DataStatus


class QuarterlyRatioPoint(BaseModel):
    quarter_end: date
    ratio_pct: float


class BuffettIndicatorResponse(BaseModel):
    current_ratio_pct: float
    as_of: datetime
    data_status: DataStatus
    source: str
    percentile_rank: float
    interpretation: str
    historical: list[QuarterlyRatioPoint]
    methodology_note: str = (
        "Approximated as the Wilshire 5000 Full Cap Price Index divided by nominal GDP "
        "(x100), following the commonly cited 'Buffett Indicator' market-cap-to-GDP "
        "heuristic. This is a market-wide valuation gauge based on a free public proxy for "
        "total market capitalization, not an exact official figure."
    )
    disclaimer: str = (
        "This describes where market valuation sits relative to its own history — it is "
        "not a prediction of future returns and not financial advice."
    )
