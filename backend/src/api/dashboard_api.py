"""
FastAPI dashboard for Gabagool trading bot.
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.trading_service import TradingService
from src.core.state_manager import StateManager
from src.api.polymarket_client import PolymarketClient
from src.config import get_config

logger = logging.getLogger(__name__)

# Response models
class StatusResponse(BaseModel):
    """Trading status response."""
    running: bool
    halted: bool
    market: Optional[dict]
    position: dict
    total_trades: int
    risk_level: str


class TradeResponse(BaseModel):
    """Trade history response."""
    trades: list
    total: int


class OrderBookResponse(BaseModel):
    """Order book response."""
    order_book: dict
    timestamp: str


class MetricsResponse(BaseModel):
    """Metrics response."""
    metrics: dict


class MessageResponse(BaseModel):
    """Generic message response."""
    success: bool
    message: str


# Create FastAPI app
app = FastAPI(
    title="Gabagool Trading Bot API",
    description="Dashboard API for Polymarket volatility arbitrage bot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global trading service instance
trading_service: Optional[TradingService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize trading service on startup."""
    global trading_service

    logger.info("Starting dashboard API...")

    # Create trading service (but don't start it automatically)
    trading_service = TradingService()

    # Optionally auto-start (set AUTO_START=true in env)
    config = get_config()
    auto_start = config.log_level == "DEBUG"  # Auto-start in debug mode

    if auto_start:
        logger.info("Auto-starting trading service...")
        asyncio.create_task(trading_service.start())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global trading_service

    logger.info("Shutting down dashboard API...")

    if trading_service:
        await trading_service.stop()


# API Endpoints

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """
    Get current trading status.

    Returns:
        Current position, market info, and trading state
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        status = await trading_service.get_status()
        return StatusResponse(**status)

    except Exception as e:
        logger.error("Error getting status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades", response_model=TradeResponse)
async def get_trades(limit: int = 20):
    """
    Get recent trade history.

    Args:
        limit: Number of trades to return (default: 20)

    Returns:
        List of recent trades
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        trades = await trading_service.state.get_recent_trades(limit)

        # Convert to dict
        trades_dict = []
        for trade in trades:
            trade_dict = trade.dict()
            # Convert Decimal to string for JSON
            for key, value in trade_dict.items():
                if isinstance(value, Decimal):
                    trade_dict[key] = str(value)
                elif isinstance(value, datetime):
                    trade_dict[key] = value.isoformat()
            trades_dict.append(trade_dict)

        total = await trading_service.state.get_trade_count()

        return TradeResponse(trades=trades_dict, total=total)

    except Exception as e:
        logger.error("Error getting trades: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orderbook", response_model=OrderBookResponse)
async def get_orderbook():
    """
    Get current order book.

    Returns:
        Current order book for active market
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        market = await trading_service.state.get_market()

        if not market:
            raise HTTPException(status_code=404, detail="No active market")

        order_book = await trading_service.client.get_market_order_book(market)

        # Convert to dict
        order_book_dict = order_book.dict()

        # Convert Decimal to string
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        order_book_dict = convert_decimals(order_book_dict)

        return OrderBookResponse(
            order_book=order_book_dict,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting order book: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market")
async def get_market():
    """
    Get current market information.

    Returns:
        Market details
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        market = await trading_service.state.get_market()

        if not market:
            raise HTTPException(status_code=404, detail="No active market")

        market_dict = market.dict()

        # Convert special types
        for key, value in market_dict.items():
            if isinstance(value, Decimal):
                market_dict[key] = str(value)
            elif isinstance(value, datetime):
                market_dict[key] = value.isoformat()

        return market_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting market: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get current trading metrics.

    Returns:
        Risk metrics and performance data
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        metrics = await trading_service.get_metrics()
        return MetricsResponse(metrics=metrics)

    except Exception as e:
        logger.error("Error getting metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/panic", response_model=MessageResponse)
async def panic_close():
    """
    Emergency close all positions.

    WARNING: This will liquidate all positions immediately!

    Returns:
        Success message
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        logger.critical("PANIC CLOSE requested via API")

        await trading_service.panic_close()

        return MessageResponse(
            success=True,
            message="Emergency liquidation initiated"
        )

    except Exception as e:
        logger.error("Error during panic close: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/halt", response_model=MessageResponse)
async def halt_trading():
    """
    Halt accumulation (stop opening new positions).

    Returns:
        Success message
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        await trading_service.halt_trading()

        return MessageResponse(
            success=True,
            message="Trading halted"
        )

    except Exception as e:
        logger.error("Error halting trading: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resume", response_model=MessageResponse)
async def resume_trading():
    """
    Resume accumulation.

    Returns:
        Success message
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        await trading_service.resume_trading()

        return MessageResponse(
            success=True,
            message="Trading resumed"
        )

    except Exception as e:
        logger.error("Error resuming trading: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/start", response_model=MessageResponse)
async def start_trading():
    """
    Start the trading service.

    Returns:
        Success message
    """
    global trading_service

    if not trading_service:
        trading_service = TradingService()

    if trading_service.is_running:
        return MessageResponse(
            success=False,
            message="Trading service already running"
        )

    try:
        # Start in background
        asyncio.create_task(trading_service.start())

        return MessageResponse(
            success=True,
            message="Trading service started"
        )

    except Exception as e:
        logger.error("Error starting trading: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stop", response_model=MessageResponse)
async def stop_trading():
    """
    Stop the trading service.

    Returns:
        Success message
    """
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    try:
        await trading_service.stop()

        return MessageResponse(
            success=True,
            message="Trading service stopped"
        )

    except Exception as e:
        logger.error("Error stopping trading: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """
    WebSocket endpoint for streaming real-time updates.

    Sends updates every second with:
    - Current position
    - Order book
    - Risk metrics
    """
    await websocket.accept()

    logger.info("WebSocket client connected")

    try:
        while True:
            if not trading_service:
                await asyncio.sleep(1.0)
                continue

            # Get current data
            status = await trading_service.get_status()
            metrics = await trading_service.get_metrics()

            # Get recent trade
            recent_trades = await trading_service.state.get_recent_trades(1)
            last_trade = recent_trades[0].dict() if recent_trades else None

            # Convert Decimal to string
            def convert_for_json(obj):
                if isinstance(obj, dict):
                    return {k: convert_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_for_json(item) for item in obj]
                elif isinstance(obj, Decimal):
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                return obj

            status = convert_for_json(status)
            metrics = convert_for_json(metrics)
            last_trade = convert_for_json(last_trade) if last_trade else None

            # Send update
            update = {
                "type": "update",
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "metrics": metrics,
                "last_trade": last_trade
            }

            await websocket.send_json(update)

            # Send every second
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "gabagool-trading-bot",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Gabagool Trading Bot",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }
