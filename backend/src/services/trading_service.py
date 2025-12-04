"""
Main trading service orchestrator.
"""

import asyncio
import logging
from typing import Optional

from src.api.polymarket_client import PolymarketClient
from src.core.state_manager import StateManager
from src.core.accumulator import Accumulator
from src.core.equalizer import Equalizer
from src.core.risk_engine import RiskEngine
from src.models.position import MarketInfo, TradingState
from src.config import get_config

logger = logging.getLogger(__name__)


class TradingService:
    """
    Main orchestrator for the Gabagool trading bot.

    Responsibilities:
    - Initialize all components
    - Select and monitor markets
    - Run accumulator, equalizer, and risk engine
    - Handle reconnections
    - Provide status for dashboard
    """

    def __init__(self):
        """Initialize trading service."""
        self.config = get_config()

        # Initialize components
        self.client = PolymarketClient()
        self.state = StateManager()

        self.accumulator: Optional[Accumulator] = None
        self.equalizer: Optional[Equalizer] = None
        self.risk_engine: Optional[RiskEngine] = None

        self.current_market: Optional[MarketInfo] = None
        self.is_running = False

        # Tasks
        self.accumulator_task: Optional[asyncio.Task] = None
        self.equalizer_task: Optional[asyncio.Task] = None
        self.risk_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the trading service."""
        logger.info("Starting Gabagool trading service...")

        try:
            # Connect to external services
            await self.client.connect()
            await self.state.connect()

            # Initialize trading components
            self.accumulator = Accumulator(self.client, self.state)
            self.equalizer = Equalizer(self.client, self.state, self.accumulator)
            self.risk_engine = RiskEngine(self.client, self.state)

            # Select market
            market = await self._select_market()

            if not market:
                logger.error("No suitable market found, cannot start trading")
                return

            self.current_market = market
            await self.state.save_market(market)

            # Start trading components
            self.is_running = True

            self.accumulator_task = asyncio.create_task(
                self.accumulator.start(market)
            )

            self.equalizer_task = asyncio.create_task(
                self.equalizer.start()
            )

            self.risk_task = asyncio.create_task(
                self.risk_engine.start()
            )

            logger.info("Trading service started successfully")
            logger.info("Market: %s", market.question)
            logger.info("Expiration: %s", market.expiration)

            # Monitor tasks
            await self._monitor_tasks()

        except Exception as e:
            logger.error("Error starting trading service: %s", e)
            await self.stop()

    async def stop(self):
        """Stop the trading service."""
        logger.info("Stopping trading service...")

        self.is_running = False

        # Stop components
        if self.accumulator:
            await self.accumulator.stop()

        if self.equalizer:
            await self.equalizer.stop()

        if self.risk_engine:
            await self.risk_engine.stop()

        # Cancel tasks
        for task in [self.accumulator_task, self.equalizer_task, self.risk_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Disconnect
        await self.client.disconnect()
        await self.state.disconnect()

        logger.info("Trading service stopped")

    async def _select_market(self) -> Optional[MarketInfo]:
        """
        Select a market to trade.

        Strategy:
        1. Look for BTC or ETH 15-minute markets
        2. Choose market expiring in 10-15 minutes
        3. Verify market has good liquidity
        """
        logger.info("Selecting market...")

        # Try BTC first, then ETH
        for asset in ["BTC", "ETH"]:
            markets = await self.client.get_15min_markets(asset)

            if markets:
                # Sort by expiration (soonest first)
                markets.sort(key=lambda m: m.expiration)

                # Choose first suitable market
                for market in markets:
                    time_to_expiry = market.time_to_expiration() / 60

                    # Prefer markets expiring in 10-15 minutes
                    if 10 <= time_to_expiry <= 15:
                        logger.info("Selected market: %s (expires in %.1f min)",
                                   market.question, time_to_expiry)
                        return market

                # If no ideal market, take the first one
                if markets:
                    market = markets[0]
                    logger.info("Selected fallback market: %s", market.question)
                    return market

        logger.warning("No suitable markets found")
        return None

    async def _monitor_tasks(self):
        """Monitor running tasks and handle failures."""
        while self.is_running:
            try:
                # Check if any task has failed
                for task_name, task in [
                    ("Accumulator", self.accumulator_task),
                    ("Equalizer", self.equalizer_task),
                    ("Risk Engine", self.risk_task)
                ]:
                    if task and task.done():
                        try:
                            exception = task.exception()
                            if exception:
                                logger.error("%s task failed: %s", task_name, exception)
                                # Attempt restart
                                await self._restart_task(task_name)
                        except asyncio.CancelledError:
                            pass

                await asyncio.sleep(5.0)

            except Exception as e:
                logger.error("Error monitoring tasks: %s", e)
                await asyncio.sleep(5.0)

    async def _restart_task(self, task_name: str):
        """Restart a failed task."""
        logger.info("Restarting %s...", task_name)

        try:
            if task_name == "Accumulator" and self.accumulator and self.current_market:
                self.accumulator_task = asyncio.create_task(
                    self.accumulator.start(self.current_market)
                )

            elif task_name == "Equalizer" and self.equalizer:
                self.equalizer_task = asyncio.create_task(
                    self.equalizer.start()
                )

            elif task_name == "Risk Engine" and self.risk_engine:
                self.risk_task = asyncio.create_task(
                    self.risk_engine.start()
                )

            logger.info("%s restarted successfully", task_name)

        except Exception as e:
            logger.error("Failed to restart %s: %s", task_name, e)

    async def get_status(self) -> dict:
        """
        Get current trading status.

        Returns:
            Status dictionary for dashboard
        """
        position = await self.state.get_position()
        market = await self.state.get_market()
        is_halted = await self.state.is_halted()
        trade_count = await self.state.get_trade_count()

        status = {
            "running": self.is_running,
            "halted": is_halted,
            "market": market.dict() if market else None,
            "position": position.dict(),
            "total_trades": trade_count,
            "risk_level": self.risk_engine.risk_level if self.risk_engine else "UNKNOWN"
        }

        return status

    async def get_metrics(self) -> dict:
        """Get current metrics."""
        return await self.state.get_metrics()

    async def panic_close(self):
        """Emergency close all positions."""
        logger.critical("PANIC CLOSE TRIGGERED")

        if self.risk_engine and self.current_market:
            await self.risk_engine.emergency_liquidation(self.current_market)

    async def halt_trading(self):
        """Halt accumulation (but keep monitoring)."""
        await self.state.set_halt_flag(True)
        logger.warning("Trading halted")

    async def resume_trading(self):
        """Resume accumulation."""
        await self.state.set_halt_flag(False)
        logger.info("Trading resumed")
