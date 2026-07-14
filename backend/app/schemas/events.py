from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DetectedEventResponse(BaseModel):
    id: int
    ticker: str
    category: str
    headline: str
    source_url: str | None
    matched_keywords: list[str]
    confidence: float
    published_at: datetime

    model_config = {"from_attributes": True}


class EventsListResponse(BaseModel):
    ticker: str
    events: list[DetectedEventResponse]
    disclaimer: str = (
        "Events are detected via transparent keyword matching against recent headlines. "
        "A detected category indicates the headline mentions that topic — it is not proof "
        "that the event caused any price movement."
    )
