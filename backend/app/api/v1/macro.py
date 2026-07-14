from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AppSettings, DbSession
from app.schemas.macro import BuffettIndicatorResponse
from app.services.macro_service import get_buffett_indicator

router = APIRouter()


@router.get("/buffett-indicator", response_model=BuffettIndicatorResponse)
def get_buffett_indicator_endpoint(db: DbSession, settings: AppSettings):
    return BuffettIndicatorResponse(**get_buffett_indicator(db, settings))
