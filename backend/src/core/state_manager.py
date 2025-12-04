"""
Redis-backed state manager for persistent trading state.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import redis.asyncio as redis

from src.models.position import Position, Trade, MarketInfo, TradingState
from src.config import get_config

logger = logging.getLogger(__name__)


class StateManager:
    """Manages trading state with Redis persistence."""

    # Redis key prefixes
    POSITION_KEY = "gabagool:position"
    TRADES_KEY = "gabagool:trades"
    MARKET_KEY = "gabagool:market"
    STATE_KEY = "gabagool:state"
    METRICS_KEY = "gabagool:metrics"

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize state manager."""
        self.config = get_config()
        self.redis = redis_client
        self._lock_script = None

    async def connect(self):
        """Connect to Redis."""
        if self.redis is None:
            self.redis = await redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis at %s", self.config.redis_url)

        # Load Lua script for atomic operations
        self._lock_script = await self.redis.script_load("""
            local key = KEYS[1]
            local value = ARGV[1]
            return redis.call('SET', key, value)
        """)

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    # Position Management

    async def get_position(self) -> Position:
        """Retrieve current position from Redis."""
        try:
            data = await self.redis.get(self.POSITION_KEY)

            if data:
                position_dict = json.loads(data)
                # Convert string decimals back to Decimal
                for key in ['qty_yes', 'cost_yes', 'avg_yes', 'qty_no', 'cost_no', 'avg_no', 'pair_cost', 'locked_profit', 'delta']:
                    if key in position_dict:
                        position_dict[key] = Decimal(position_dict[key])

                return Position(**position_dict)

            return Position()

        except Exception as e:
            logger.error("Error retrieving position: %s", e)
            return Position()

    async def save_position(self, position: Position) -> bool:
        """Save position to Redis atomically."""
        try:
            position.last_updated = datetime.utcnow()

            # Convert to JSON-serializable dict
            position_dict = position.dict()
            for key, value in position_dict.items():
                if isinstance(value, Decimal):
                    position_dict[key] = str(value)
                elif isinstance(value, datetime):
                    position_dict[key] = value.isoformat()

            await self.redis.set(
                self.POSITION_KEY,
                json.dumps(position_dict)
            )

            logger.debug("Position saved: %s", position_dict)
            return True

        except Exception as e:
            logger.error("Error saving position: %s", e)
            return False

    async def update_position_atomic(
        self,
        side: str,
        qty_delta: Decimal,
        cost_delta: Decimal
    ) -> Position:
        """Atomically update position."""
        async with self.redis.pipeline(transaction=True) as pipe:
            try:
                # Watch the position key for changes
                await pipe.watch(self.POSITION_KEY)

                # Get current position
                position = await self.get_position()

                # Update based on side
                if side == "YES":
                    position.qty_yes += qty_delta
                    position.cost_yes += cost_delta
                elif side == "NO":
                    position.qty_no += qty_delta
                    position.cost_no += cost_delta

                # Recalculate derived fields
                position = Position(**position.dict())

                # Save updated position
                position_dict = position.dict()
                for key, value in position_dict.items():
                    if isinstance(value, Decimal):
                        position_dict[key] = str(value)
                    elif isinstance(value, datetime):
                        position_dict[key] = value.isoformat()

                pipe.multi()
                await pipe.set(self.POSITION_KEY, json.dumps(position_dict))
                await pipe.execute()

                logger.info("Position updated atomically: %s %s shares @ cost %s",
                           side, qty_delta, cost_delta)

                return position

            except redis.WatchError:
                logger.warning("Position update conflict, retrying...")
                # Retry on conflict
                return await self.update_position_atomic(side, qty_delta, cost_delta)

    # Trade History

    async def add_trade(self, trade: Trade) -> bool:
        """Add a trade to history."""
        try:
            trade_dict = trade.dict()
            for key, value in trade_dict.items():
                if isinstance(value, Decimal):
                    trade_dict[key] = str(value)
                elif isinstance(value, datetime):
                    trade_dict[key] = value.isoformat()

            # Add to sorted set with timestamp as score
            timestamp = trade.timestamp.timestamp()
            await self.redis.zadd(
                self.TRADES_KEY,
                {json.dumps(trade_dict): timestamp}
            )

            # Keep only last 1000 trades
            await self.redis.zremrangebyrank(self.TRADES_KEY, 0, -1001)

            logger.info("Trade recorded: %s", trade.trade_id)
            return True

        except Exception as e:
            logger.error("Error adding trade: %s", e)
            return False

    async def get_recent_trades(self, limit: int = 20) -> List[Trade]:
        """Get recent trades."""
        try:
            # Get last N trades (newest first)
            trades_data = await self.redis.zrevrange(
                self.TRADES_KEY,
                0,
                limit - 1,
                withscores=False
            )

            trades = []
            for trade_json in trades_data:
                trade_dict = json.loads(trade_json)

                # Convert strings back to proper types
                for key in ['price', 'qty', 'resulting_pair_cost', 'resulting_delta']:
                    if key in trade_dict:
                        trade_dict[key] = Decimal(trade_dict[key])

                if 'timestamp' in trade_dict:
                    trade_dict['timestamp'] = datetime.fromisoformat(trade_dict['timestamp'])

                trades.append(Trade(**trade_dict))

            return trades

        except Exception as e:
            logger.error("Error retrieving trades: %s", e)
            return []

    async def get_trade_count(self) -> int:
        """Get total number of trades."""
        try:
            return await self.redis.zcard(self.TRADES_KEY)
        except Exception as e:
            logger.error("Error getting trade count: %s", e)
            return 0

    # Market Management

    async def save_market(self, market: MarketInfo) -> bool:
        """Save current market info."""
        try:
            market_dict = market.dict()
            for key, value in market_dict.items():
                if isinstance(value, Decimal):
                    market_dict[key] = str(value)
                elif isinstance(value, datetime):
                    market_dict[key] = value.isoformat()

            await self.redis.set(
                self.MARKET_KEY,
                json.dumps(market_dict)
            )

            logger.info("Market saved: %s", market.market_id)
            return True

        except Exception as e:
            logger.error("Error saving market: %s", e)
            return False

    async def get_market(self) -> Optional[MarketInfo]:
        """Retrieve current market info."""
        try:
            data = await self.redis.get(self.MARKET_KEY)

            if data:
                market_dict = json.loads(data)

                # Convert strings back to proper types
                if 'strike_price' in market_dict and market_dict['strike_price']:
                    market_dict['strike_price'] = Decimal(market_dict['strike_price'])
                if 'min_tick_size' in market_dict:
                    market_dict['min_tick_size'] = Decimal(market_dict['min_tick_size'])
                if 'min_size' in market_dict:
                    market_dict['min_size'] = Decimal(market_dict['min_size'])
                if 'expiration' in market_dict:
                    market_dict['expiration'] = datetime.fromisoformat(market_dict['expiration'])

                return MarketInfo(**market_dict)

            return None

        except Exception as e:
            logger.error("Error retrieving market: %s", e)
            return None

    # Trading State

    async def save_state(self, state: TradingState) -> bool:
        """Save overall trading state."""
        try:
            state_dict = state.dict()

            # Convert complex types
            def convert_value(value):
                if isinstance(value, Decimal):
                    return str(value)
                elif isinstance(value, datetime):
                    return value.isoformat()
                elif isinstance(value, dict):
                    return {k: convert_value(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [convert_value(v) for v in value]
                return value

            state_dict = {k: convert_value(v) for k, v in state_dict.items()}

            await self.redis.set(
                self.STATE_KEY,
                json.dumps(state_dict)
            )

            return True

        except Exception as e:
            logger.error("Error saving state: %s", e)
            return False

    async def get_state(self) -> TradingState:
        """Retrieve trading state."""
        try:
            data = await self.redis.get(self.STATE_KEY)

            if data:
                state_dict = json.loads(data)

                # The TradingState model will handle nested Position/Market conversion
                return TradingState(**state_dict)

            return TradingState()

        except Exception as e:
            logger.error("Error retrieving state: %s", e)
            return TradingState()

    async def set_halt_flag(self, halted: bool) -> bool:
        """Set trading halt flag."""
        try:
            await self.redis.set("gabagool:halt", "1" if halted else "0")
            logger.info("Halt flag set to: %s", halted)
            return True
        except Exception as e:
            logger.error("Error setting halt flag: %s", e)
            return False

    async def is_halted(self) -> bool:
        """Check if trading is halted."""
        try:
            value = await self.redis.get("gabagool:halt")
            return value == "1"
        except Exception as e:
            logger.error("Error checking halt flag: %s", e)
            return False

    # Metrics

    async def update_metrics(self, metrics: dict) -> bool:
        """Update trading metrics."""
        try:
            # Convert Decimal values
            for key, value in metrics.items():
                if isinstance(value, Decimal):
                    metrics[key] = str(value)
                elif isinstance(value, datetime):
                    metrics[key] = value.isoformat()

            await self.redis.hset(
                self.METRICS_KEY,
                mapping=metrics
            )

            return True

        except Exception as e:
            logger.error("Error updating metrics: %s", e)
            return False

    async def get_metrics(self) -> dict:
        """Retrieve trading metrics."""
        try:
            metrics = await self.redis.hgetall(self.METRICS_KEY)
            return metrics or {}
        except Exception as e:
            logger.error("Error retrieving metrics: %s", e)
            return {}

    async def clear_all(self) -> bool:
        """Clear all trading data (use with caution!)."""
        try:
            await self.redis.delete(
                self.POSITION_KEY,
                self.TRADES_KEY,
                self.MARKET_KEY,
                self.STATE_KEY,
                self.METRICS_KEY,
                "gabagool:halt"
            )
            logger.warning("All trading data cleared!")
            return True
        except Exception as e:
            logger.error("Error clearing data: %s", e)
            return False
