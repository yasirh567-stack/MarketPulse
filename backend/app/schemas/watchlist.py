from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class WatchlistItemResponse(BaseModel):
    ticker: str
    added_at: datetime

    model_config = {"from_attributes": True}


class WatchlistResponse(BaseModel):
    watchlist_id: int
    owner_key: str
    items: list[WatchlistItemResponse]


class AddWatchlistItemRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not v or len(v) > 10 or not v.replace(".", "").isalnum():
            raise ValueError("Invalid ticker symbol")
        return v
