"""
Main accumulation algorithm for Gabagool volatility arbitrage.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.models.position import Position, OrderBook, MarketInfo, Trade
from src.api.polymarket_client import PolymarketClient
from src.core.state_manager import StateManager
from src.config import get_config

logger = logging.getLogger(__name__)


class Accumulator:
    """
    Main trading algorithm that accumulates paired positions
    when opportunities arise.
    """

    def __init__(
        self,
        client: PolymarketClient,
        state_manager: StateManager
    ):
        """Initialize accumulator."""
        self.client = client
        self.state = state_manager
        self.config = get_config()

        self.is_running = False
        self.current_market: Optional[MarketInfo] = None

    async def start(self, market: MarketInfo):
        """Start the accumulation algorithm."""
        self.current_market = market
        self.is_running = True

        await self.state.save_market(market)
        logger.info("Accumulator started for market: %s", market.question)

        # Main loop
        while self.is_running:
            try:
                # Check if halted
                if await self.state.is_halted():
                    logger.info("Trading halted, pausing accumulation")
                    await asyncio.sleep(1.0)
                    continue

                # Check settlement buffer
                if market.is_within_settlement_buffer(self.config.settlement_buffer_seconds):
                    logger.warning("Within settlement buffer, stopping accumulation")
                    self.is_running = False
                    break

                # Scan for opportunities
                await self._scan_and_execute()

                # Sleep for configured interval
                await asyncio.sleep(self.config.get_scan_interval_seconds())

            except Exception as e:
                logger.error("Error in accumulation loop: %s", e)
                await asyncio.sleep(1.0)

    async def stop(self):
        """Stop the accumulation algorithm."""
        self.is_running = False
        logger.info("Accumulator stopped")

    async def _scan_and_execute(self):
        """
        Scan for arbitrage opportunities and execute trades.

        Logic:
        1. Get current position and order book
        2. Calculate state (avg prices, pair cost, delta)
        3. Check if Ask_YES + avg_NO < 0.98 or Ask_NO + avg_YES < 0.98
        4. Verify constraints (delta, liquidity)
        5. Execute trade if opportunity exists
        """
        if not self.current_market:
            return

        # Get current state
        position = await self.state.get_position()
        order_book = await self.client.get_market_order_book(self.current_market)

        if not order_book.yes_asks or not order_book.no_asks:
            logger.debug("Incomplete order book, skipping scan")
            return

        # Calculate current state
        state_info = self.calculate_state(position)

        avg_yes = state_info["avg_yes"]
        avg_no = state_info["avg_no"]
        pair_cost = state_info["pair_cost"]
        delta = state_info["delta"]

        # Get best ask prices
        ask_yes = order_book.get_best_ask_yes()
        ask_no = order_book.get_best_ask_no()

        if not ask_yes or not ask_no:
            return

        # Target pair cost (1.00 - profit_margin)
        target_cost = self.config.get_profit_target()

        # Check for opportunities
        opportunity_yes = None
        opportunity_no = None

        # Opportunity to buy YES
        if ask_yes + avg_no < target_cost:
            opportunity_yes = {
                "side": "YES",
                "price": ask_yes,
                "expected_pair_cost": ask_yes + avg_no
            }

        # Opportunity to buy NO
        if ask_no + avg_yes < target_cost:
            opportunity_no = {
                "side": "NO",
                "price": ask_no,
                "expected_pair_cost": ask_no + avg_yes
            }

        # Execute best opportunity
        if opportunity_yes and opportunity_no:
            # Choose the better opportunity
            if opportunity_yes["expected_pair_cost"] < opportunity_no["expected_pair_cost"]:
                await self._execute_opportunity(opportunity_yes, position, order_book)
            else:
                await self._execute_opportunity(opportunity_no, position, order_book)

        elif opportunity_yes:
            await self._execute_opportunity(opportunity_yes, position, order_book)

        elif opportunity_no:
            await self._execute_opportunity(opportunity_no, position, order_book)

    async def _execute_opportunity(
        self,
        opportunity: dict,
        position: Position,
        order_book: OrderBook
    ):
        """Execute a trading opportunity."""
        side = opportunity["side"]
        price = opportunity["price"]

        # Check constraints before executing
        if not await self._check_constraints(side, position, order_book):
            logger.debug("Constraints not met for %s trade", side)
            return

        # Execute trade
        await self.execute_trade(
            side=side,
            price=price,
            qty=self.config.trade_size
        )

    def calculate_state(self, position: Position) -> dict:
        """
        Calculate current position state.

        Returns:
            Dict with avg_yes, avg_no, pair_cost, delta, locked_profit
        """
        avg_yes = Decimal("0")
        avg_no = Decimal("0")

        if position.qty_yes > 0:
            avg_yes = position.cost_yes / position.qty_yes

        if position.qty_no > 0:
            avg_no = position.cost_no / position.qty_no

        pair_cost = avg_yes + avg_no
        delta = position.qty_yes - position.qty_no

        # Calculate locked profit
        paired_qty = min(position.qty_yes, position.qty_no)
        locked_profit = Decimal("0")

        if paired_qty > 0 and pair_cost < Decimal("1.00"):
            locked_profit = paired_qty * (Decimal("1.00") - pair_cost)

        return {
            "avg_yes": avg_yes,
            "avg_no": avg_no,
            "pair_cost": pair_cost,
            "delta": delta,
            "locked_profit": locked_profit,
        }

    async def _check_constraints(
        self,
        side: str,
        position: Position,
        order_book: OrderBook
    ) -> bool:
        """
        Check if trade meets all constraints.

        Constraints:
        1. Delta constraint: abs(delta + trade) <= MAX_UNHEDGED_DELTA
        2. Liquidity constraint: Opposite side has 3x liquidity available
        """
        # 1. Check delta constraint
        current_delta = position.delta
        trade_size = self.config.trade_size

        new_delta = current_delta + trade_size if side == "YES" else current_delta - trade_size

        if abs(new_delta) > self.config.max_unhedged_delta:
            logger.debug("Delta constraint violated: new_delta=%s, max=%s",
                        new_delta, self.config.max_unhedged_delta)
            return False

        # 2. Check liquidity constraint
        opposite_side = "NO" if side == "YES" else "YES"
        required_liquidity = trade_size * self.config.min_liquidity_multiplier

        available_liquidity = order_book.get_depth(
            side=opposite_side,
            bid_or_ask="ASK",
            max_levels=5
        )

        if available_liquidity < required_liquidity:
            logger.debug("Liquidity constraint violated: available=%s, required=%s",
                        available_liquidity, required_liquidity)
            return False

        return True

    async def execute_trade(
        self,
        side: str,
        price: Decimal,
        qty: Decimal
    ) -> Optional[Trade]:
        """
        Execute a trade.

        Args:
            side: "YES" or "NO"
            price: Limit price
            qty: Quantity to trade

        Returns:
            Trade object if successful
        """
        if not self.current_market:
            return None

        try:
            # Determine token ID
            token_id = (
                self.current_market.token_id_yes
                if side == "YES"
                else self.current_market.token_id_no
            )

            # Place limit order (post-only to avoid taker fees)
            order_id = await self.client.place_limit_order(
                token_id=token_id,
                side="BUY",
                price=price,
                size=qty,
                post_only=True
            )

            if not order_id:
                logger.error("Failed to place order")
                return None

            # Update position
            cost = price * qty
            updated_position = await self.state.update_position_atomic(
                side=side,
                qty_delta=qty,
                cost_delta=cost
            )

            # Calculate resulting state
            state = self.calculate_state(updated_position)

            # Create trade record
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                side=side,
                price=price,
                qty=qty,
                resulting_pair_cost=state["pair_cost"],
                resulting_delta=state["delta"],
                order_id=order_id,
                market_id=self.current_market.market_id
            )

            # Save trade
            await self.state.add_trade(trade)

            logger.info("Trade executed: %s %s @ %s, pair_cost=%s, delta=%s",
                       side, qty, price, state["pair_cost"], state["delta"])

            return trade

        except Exception as e:
            logger.error("Error executing trade: %s", e)
            return None

    def scan_opportunities(
        self,
        position: Position,
        order_book: OrderBook
    ) -> list:
        """
        Scan for arbitrage opportunities.

        Returns:
            List of opportunities with expected pair cost
        """
        opportunities = []

        state = self.calculate_state(position)
        avg_yes = state["avg_yes"]
        avg_no = state["avg_no"]

        ask_yes = order_book.get_best_ask_yes()
        ask_no = order_book.get_best_ask_no()

        if not ask_yes or not ask_no:
            return opportunities

        target_cost = self.config.get_profit_target()

        # Check YES opportunity
        if ask_yes + avg_no < target_cost:
            opportunities.append({
                "side": "YES",
                "price": ask_yes,
                "expected_pair_cost": ask_yes + avg_no,
                "profit": target_cost - (ask_yes + avg_no)
            })

        # Check NO opportunity
        if ask_no + avg_yes < target_cost:
            opportunities.append({
                "side": "NO",
                "price": ask_no,
                "expected_pair_cost": ask_no + avg_yes,
                "profit": target_cost - (ask_no + avg_yes)
            })

        return opportunities
