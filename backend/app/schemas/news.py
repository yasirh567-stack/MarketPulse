from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import DataStatus


class NewsArticleResponse(BaseModel):
    id: int
    ticker: str
    title: str
    summary: str | None
    url: str
    source: str
    published_at: datetime
    data_status: DataStatus

    model_config = {"from_attributes": True}


class NewsListResponse(BaseModel):
    ticker: str
    total: int
    page: int
    page_size: int
    articles: list[NewsArticleResponse]
