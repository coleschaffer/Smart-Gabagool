"""
Equalizer algorithm for rebalancing positions.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Optional

from src.models.position import Position, OrderBook, MarketInfo
from src.api.polymarket_client import PolymarketClient
from src.core.state_manager import StateManager
from src.core.accumulator import Accumulator
from src.config import get_config

logger = logging.getLogger(__name__)


class Equalizer:
    """
    Rebalancing algorithm that eliminates position delta
    by aggressively bidding on the lagging side.
    """

    def __init__(
        self,
        client: PolymarketClient,
        state_manager: StateManager,
        accumulator: Accumulator
    ):
        """Initialize equalizer."""
        self.client = client
        self.state = state_manager
        self.accumulator = accumulator
        self.config = get_config()

        self.is_running = False

    async def start(self):
        """Start the equalization monitoring."""
        self.is_running = True
        logger.info("Equalizer started")

        while self.is_running:
            try:
                # Check if halted
                if await self.state.is_halted():
                    await asyncio.sleep(1.0)
                    continue

                # Check for imbalance
                await self._check_and_rebalance()

                # Check every second
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error("Error in equalizer loop: %s", e)
                await asyncio.sleep(1.0)

    async def stop(self):
        """Stop the equalizer."""
        self.is_running = False
        logger.info("Equalizer stopped")

    async def _check_and_rebalance(self):
        """Check for position imbalance and rebalance if needed."""
        # Get current position
        position = await self.state.get_position()

        # Calculate delta
        delta = position.delta

        # If delta is zero or small, no action needed
        if abs(delta) < Decimal("1"):
            return

        logger.info("Position imbalance detected: delta=%s", delta)

        # Get current market
        market = await self.state.get_market()
        if not market:
            logger.warning("No market set, cannot rebalance")
            return

        # Get order book
        order_book = await self.client.get_market_order_book(market)

        # Determine lagging side
        lagging_side = "NO" if delta > 0 else "YES"

        # Calculate target quantity to balance
        target_qty = abs(delta)

        # Execute rebalancing trades
        await self._rebalance_position(
            lagging_side=lagging_side,
            target_qty=target_qty,
            position=position,
            order_book=order_book,
            market=market
        )

    async def _rebalance_position(
        self,
        lagging_side: str,
        target_qty: Decimal,
        position: Position,
        order_book: OrderBook,
        market: MarketInfo
    ):
        """
        Rebalance position by buying the lagging side.

        Strategy:
        1. Bid aggressively (at or above best ask)
        2. Ensure total pair cost stays < 1.00
        3. Trade in chunks if necessary
        """
        # Get current averages
        state = self.accumulator.calculate_state(position)
        avg_yes = state["avg_yes"]
        avg_no = state["avg_no"]

        # Determine max price we can pay
        if lagging_side == "YES":
            opposite_avg = avg_no
            best_ask = order_book.get_best_ask_yes()
        else:
            opposite_avg = avg_yes
            best_ask = order_book.get_best_ask_no()

        if not best_ask:
            logger.warning("No ask available for %s", lagging_side)
            return

        # Calculate maximum price to keep pair cost < 1.00
        max_price = Decimal("0.99") - opposite_avg

        if max_price <= 0:
            logger.error("Cannot rebalance: max_price=%s is non-positive", max_price)
            return

        # Use aggressive price (best ask or slightly better)
        bid_price = min(best_ask, max_price)

        # Trade in chunks
        chunk_size = min(target_qty, self.config.trade_size)
        remaining = target_qty

        while remaining > 0 and self.is_running:
            try:
                trade_qty = min(remaining, chunk_size)

                # Execute trade using accumulator
                trade = await self.accumulator.execute_trade(
                    side=lagging_side,
                    price=bid_price,
                    qty=trade_qty
                )

                if trade:
                    remaining -= trade_qty
                    logger.info("Rebalance trade executed: %s %s @ %s, remaining=%s",
                               lagging_side, trade_qty, bid_price, remaining)
                else:
                    logger.warning("Rebalance trade failed, retrying...")
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error("Error in rebalance trade: %s", e)
                await asyncio.sleep(0.5)

    async def force_rebalance(self):
        """
        Force immediate rebalancing (called manually or by risk engine).
        """
        logger.info("Force rebalance triggered")
        await self._check_and_rebalance()

    def calculate_rebalance_cost(
        self,
        position: Position,
        order_book: OrderBook
    ) -> dict:
        """
        Calculate the cost to rebalance current position.

        Returns:
            Dict with side, qty, estimated_price, estimated_cost
        """
        delta = position.delta

        if abs(delta) < Decimal("1"):
            return {
                "needed": False,
                "delta": delta
            }

        lagging_side = "NO" if delta > 0 else "YES"
        target_qty = abs(delta)

        # Get best ask
        if lagging_side == "YES":
            best_ask = order_book.get_best_ask_yes()
        else:
            best_ask = order_book.get_best_ask_no()

        estimated_cost = best_ask * target_qty if best_ask else None

        return {
            "needed": True,
            "delta": delta,
            "side": lagging_side,
            "qty": target_qty,
            "estimated_price": best_ask,
            "estimated_cost": estimated_cost
        }
