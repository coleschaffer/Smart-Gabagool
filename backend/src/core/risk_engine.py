"""
Risk management engine for Gabagool trading bot.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Optional, Literal

from src.models.position import Position, OrderBook, MarketInfo, RiskMetrics
from src.api.polymarket_client import PolymarketClient
from src.core.state_manager import StateManager
from src.config import get_config

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Risk management and monitoring engine.

    Responsibilities:
    - Monitor position delta
    - Check liquidity depth
    - Implement stop-loss mechanisms
    - Handle emergency liquidation
    - Monitor settlement buffer
    """

    def __init__(
        self,
        client: PolymarketClient,
        state_manager: StateManager
    ):
        """Initialize risk engine."""
        self.client = client
        self.state = state_manager
        self.config = get_config()

        self.is_running = False
        self.risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"

    async def start(self):
        """Start risk monitoring."""
        self.is_running = True
        logger.info("Risk engine started")

        while self.is_running:
            try:
                # Run risk checks
                await self._run_risk_checks()

                # Check every 5 seconds
                await asyncio.sleep(5.0)

            except Exception as e:
                logger.error("Error in risk engine: %s", e)
                await asyncio.sleep(5.0)

    async def stop(self):
        """Stop risk monitoring."""
        self.is_running = False
        logger.info("Risk engine stopped")

    async def _run_risk_checks(self):
        """Run all risk checks."""
        # Get current state
        position = await self.state.get_position()
        market = await self.state.get_market()

        if not market:
            return

        order_book = await self.client.get_market_order_book(market)

        # 1. Check delta constraint
        delta_risk = self.check_max_delta(position)

        # 2. Check liquidity depth
        liquidity_risk = self.check_liquidity_depth(position, order_book)

        # 3. Check stop-loss
        stop_loss_triggered = await self.check_bailout_stop_loss(position, order_book, market)

        # 4. Check settlement buffer
        settlement_risk = self.check_settlement_buffer(market)

        # Calculate overall risk level
        self._update_risk_level(delta_risk, liquidity_risk, stop_loss_triggered, settlement_risk)

        # Update metrics
        metrics = self.get_risk_metrics(position, order_book, market)
        await self.state.update_metrics(metrics.dict())

        # Take action if needed
        if stop_loss_triggered:
            logger.critical("STOP LOSS TRIGGERED - Initiating emergency liquidation")
            await self.emergency_liquidation(market)

        elif settlement_risk:
            logger.warning("Settlement buffer reached - Halting accumulation")
            await self.state.set_halt_flag(True)

    def check_max_delta(self, position: Position) -> bool:
        """
        Check if position delta exceeds maximum.

        Returns:
            True if delta is within limits, False otherwise
        """
        delta = abs(position.delta)
        max_delta = self.config.max_unhedged_delta

        if delta > max_delta:
            logger.warning("Delta constraint violated: delta=%s, max=%s", delta, max_delta)
            return False

        return True

    def check_liquidity_depth(
        self,
        position: Position,
        order_book: OrderBook
    ) -> bool:
        """
        Check if there's sufficient liquidity to close position.

        Returns:
            True if liquidity is sufficient, False otherwise
        """
        # Check liquidity on both sides
        yes_liquidity = order_book.get_depth("YES", "ASK", max_levels=10)
        no_liquidity = order_book.get_depth("NO", "ASK", max_levels=10)

        # Need enough liquidity to close position
        required_yes = position.qty_yes
        required_no = position.qty_no

        if yes_liquidity < required_yes:
            logger.warning("Insufficient YES liquidity: have=%s, need=%s",
                          yes_liquidity, required_yes)
            return False

        if no_liquidity < required_no:
            logger.warning("Insufficient NO liquidity: have=%s, need=%s",
                          no_liquidity, required_no)
            return False

        return True

    async def check_bailout_stop_loss(
        self,
        position: Position,
        order_book: OrderBook,
        market: MarketInfo
    ) -> bool:
        """
        Check if bailout stop-loss should trigger.

        Stop-loss triggers if:
        - Mark price implies >2% loss on position
        - Large adverse price movement

        Returns:
            True if stop-loss should trigger
        """
        # Calculate mark-to-market value
        mid_yes = self._get_mid_price(order_book.yes_bids, order_book.yes_asks)
        mid_no = self._get_mid_price(order_book.no_bids, order_book.no_asks)

        if not mid_yes or not mid_no:
            return False

        # Current position value
        position_value = (position.qty_yes * mid_yes) + (position.qty_no * mid_no)
        position_cost = position.cost_yes + position.cost_no

        # Calculate unrealized P&L
        unrealized_pnl = position_value - position_cost

        # Check if loss exceeds threshold
        loss_threshold = position_cost * (self.config.bailout_stop_loss_percent / Decimal("100"))

        if unrealized_pnl < -loss_threshold:
            logger.critical("Stop-loss triggered: unrealized_pnl=%s, threshold=%s",
                           unrealized_pnl, -loss_threshold)
            return True

        return False

    def check_settlement_buffer(self, market: MarketInfo) -> bool:
        """
        Check if we're within settlement buffer.

        Returns:
            True if within buffer (trading should stop)
        """
        return market.is_within_settlement_buffer(self.config.settlement_buffer_seconds)

    async def emergency_liquidation(self, market: MarketInfo):
        """
        Emergency liquidation: sell all positions immediately.

        Strategy:
        1. Cancel all open orders
        2. Sell all YES and NO shares at market
        3. Accept taker fees for immediate execution
        """
        logger.critical("EMERGENCY LIQUIDATION INITIATED")

        try:
            # 1. Cancel all open orders
            await self._cancel_all_orders()

            # 2. Get current position
            position = await self.state.get_position()

            # 3. Sell all shares
            if position.qty_yes > 0:
                await self._market_sell(
                    token_id=market.token_id_yes,
                    qty=position.qty_yes,
                    side="YES"
                )

            if position.qty_no > 0:
                await self._market_sell(
                    token_id=market.token_id_no,
                    qty=position.qty_no,
                    side="NO"
                )

            # 4. Halt trading
            await self.state.set_halt_flag(True)

            logger.critical("Emergency liquidation completed")

        except Exception as e:
            logger.critical("Error during emergency liquidation: %s", e)

    async def _cancel_all_orders(self):
        """Cancel all open orders."""
        try:
            orders = await self.client.get_open_orders()

            for order in orders:
                order_id = order.get("orderID")
                if order_id:
                    await self.client.cancel_order(order_id)

            logger.info("Cancelled %d open orders", len(orders))

        except Exception as e:
            logger.error("Error cancelling orders: %s", e)

    async def _market_sell(self, token_id: str, qty: Decimal, side: str):
        """
        Execute market sell (aggressive limit order at bid price).

        Args:
            token_id: Token to sell
            qty: Quantity to sell
            side: "YES" or "NO"
        """
        try:
            # Get current order book
            order_book_data = await self.client.get_order_book(token_id)

            if not order_book_data:
                logger.error("Cannot market sell: no order book data")
                return

            # Get best bid (we're selling, so we hit the bid)
            best_bid = order_book_data[0].price if order_book_data else Decimal("0.01")

            # Place aggressive sell order
            order_id = await self.client.place_limit_order(
                token_id=token_id,
                side="SELL",
                price=best_bid,
                size=qty,
                post_only=False  # Allow taker order for immediate execution
            )

            if order_id:
                logger.info("Market sell executed: %s %s @ %s", side, qty, best_bid)

                # Update position
                await self.state.update_position_atomic(
                    side=side,
                    qty_delta=-qty,
                    cost_delta=-(best_bid * qty)
                )

        except Exception as e:
            logger.error("Error in market sell: %s", e)

    def _get_mid_price(
        self,
        bids: list,
        asks: list
    ) -> Optional[Decimal]:
        """Calculate mid price from bids and asks."""
        if not bids or not asks:
            return None

        best_bid = bids[0].price
        best_ask = asks[0].price

        return (best_bid + best_ask) / Decimal("2")

    def _update_risk_level(
        self,
        delta_ok: bool,
        liquidity_ok: bool,
        stop_loss: bool,
        settlement_risk: bool
    ):
        """Update overall risk level."""
        if stop_loss:
            self.risk_level = "CRITICAL"
        elif not delta_ok or not liquidity_ok:
            self.risk_level = "HIGH"
        elif settlement_risk:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "LOW"

    def get_risk_metrics(
        self,
        position: Position,
        order_book: OrderBook,
        market: MarketInfo
    ) -> RiskMetrics:
        """
        Calculate current risk metrics.

        Returns:
            RiskMetrics object
        """
        # Calculate unrealized P&L
        mid_yes = self._get_mid_price(order_book.yes_bids, order_book.yes_asks)
        mid_no = self._get_mid_price(order_book.no_bids, order_book.no_asks)

        unrealized_pnl = Decimal("0")
        if mid_yes and mid_no:
            position_value = (position.qty_yes * mid_yes) + (position.qty_no * mid_no)
            position_cost = position.cost_yes + position.cost_no
            unrealized_pnl = position_value - position_cost

        # Calculate liquidity depths
        liquidity_yes = order_book.get_depth("YES", "ASK", max_levels=10)
        liquidity_no = order_book.get_depth("NO", "ASK", max_levels=10)

        return RiskMetrics(
            current_delta=position.delta,
            max_delta=self.config.max_unhedged_delta,
            pair_cost=position.pair_cost,
            locked_profit=position.locked_profit,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=Decimal("0"),  # TODO: Calculate from trade history
            time_to_settlement=market.time_to_expiration(),
            liquidity_depth_yes=liquidity_yes,
            liquidity_depth_no=liquidity_no,
            risk_level=self.risk_level
        )

    async def force_halt(self):
        """Force halt trading."""
        await self.state.set_halt_flag(True)
        logger.warning("Trading forcibly halted")

    async def resume_trading(self):
        """Resume trading."""
        await self.state.set_halt_flag(False)
        logger.info("Trading resumed")
