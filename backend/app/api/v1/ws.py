from __future__ import annotations

from fastapi import APIRouter, WebSocket

from app.websocket.manager import MarketWebSocketConnection

router = APIRouter()


@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket) -> None:
    connection = MarketWebSocketConnection(websocket)
    await connection.handle()
