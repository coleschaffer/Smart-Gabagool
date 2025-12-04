"""
Position and trading models for Gabagool volatility arbitrage bot.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, validator


class Position(BaseModel):
    """Represents the current trading position."""

    qty_yes: Decimal = Field(default=Decimal("0"), description="Quantity of YES shares held")
    cost_yes: Decimal = Field(default=Decimal("0"), description="Total cost of YES shares")
    avg_yes: Decimal = Field(default=Decimal("0"), description="Average price paid for YES shares")

    qty_no: Decimal = Field(default=Decimal("0"), description="Quantity of NO shares held")
    cost_no: Decimal = Field(default=Decimal("0"), description="Total cost of NO shares")
    avg_no: Decimal = Field(default=Decimal("0"), description="Average price paid for NO shares")

    pair_cost: Decimal = Field(default=Decimal("0"), description="Cost to build paired position")
    locked_profit: Decimal = Field(default=Decimal("0"), description="Guaranteed profit on paired shares")
    delta: Decimal = Field(default=Decimal("0"), description="Unhedged position (qty_yes - qty_no)")

    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

    @validator('avg_yes', 'avg_no', always=True)
    def calculate_averages(cls, v, values, field):
        """Calculate average prices from quantities and costs."""
        if field.name == 'avg_yes':
            qty = values.get('qty_yes', Decimal("0"))
            cost = values.get('cost_yes', Decimal("0"))
        else:
            qty = values.get('qty_no', Decimal("0"))
            cost = values.get('cost_no', Decimal("0"))

        if qty > 0:
            return cost / qty
        return Decimal("0")

    @validator('delta', always=True)
    def calculate_delta(cls, v, values):
        """Calculate position delta."""
        qty_yes = values.get('qty_yes', Decimal("0"))
        qty_no = values.get('qty_no', Decimal("0"))
        return qty_yes - qty_no

    @validator('pair_cost', always=True)
    def calculate_pair_cost(cls, v, values):
        """Calculate the cost to build paired position."""
        avg_yes = values.get('avg_yes', Decimal("0"))
        avg_no = values.get('avg_no', Decimal("0"))
        return avg_yes + avg_no

    @validator('locked_profit', always=True)
    def calculate_locked_profit(cls, v, values):
        """Calculate locked profit on paired shares."""
        qty_yes = values.get('qty_yes', Decimal("0"))
        qty_no = values.get('qty_no', Decimal("0"))
        pair_cost = values.get('pair_cost', Decimal("0"))

        paired_qty = min(qty_yes, qty_no)
        if paired_qty > 0 and pair_cost < Decimal("1.00"):
            return paired_qty * (Decimal("1.00") - pair_cost)
        return Decimal("0")


class OrderBookEntry(BaseModel):
    """Single order book entry."""

    price: Decimal = Field(..., description="Price level")
    size: Decimal = Field(..., description="Size available at this level")

    class Config:
        json_encoders = {
            Decimal: str
        }


class OrderBook(BaseModel):
    """Order book for YES and NO sides."""

    yes_bids: List[OrderBookEntry] = Field(default_factory=list, description="YES side bids")
    yes_asks: List[OrderBookEntry] = Field(default_factory=list, description="YES side asks")
    no_bids: List[OrderBookEntry] = Field(default_factory=list, description="NO side bids")
    no_asks: List[OrderBookEntry] = Field(default_factory=list, description="NO side asks")

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

    def get_best_ask_yes(self) -> Optional[Decimal]:
        """Get best ask price on YES side."""
        return self.yes_asks[0].price if self.yes_asks else None

    def get_best_ask_no(self) -> Optional[Decimal]:
        """Get best ask price on NO side."""
        return self.no_asks[0].price if self.no_asks else None

    def get_best_bid_yes(self) -> Optional[Decimal]:
        """Get best bid price on YES side."""
        return self.yes_bids[0].price if self.yes_bids else None

    def get_best_bid_no(self) -> Optional[Decimal]:
        """Get best bid price on NO side."""
        return self.no_bids[0].price if self.no_bids else None

    def get_depth(self, side: Literal["YES", "NO"], bid_or_ask: Literal["BID", "ASK"], max_levels: int = 5) -> Decimal:
        """Calculate total liquidity depth."""
        if side == "YES":
            entries = self.yes_bids if bid_or_ask == "BID" else self.yes_asks
        else:
            entries = self.no_bids if bid_or_ask == "BID" else self.no_asks

        total_size = Decimal("0")
        for entry in entries[:max_levels]:
            total_size += entry.size

        return total_size


class Trade(BaseModel):
    """Represents a completed trade."""

    trade_id: str = Field(..., description="Unique trade identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    side: Literal["YES", "NO"] = Field(..., description="Trade side")
    price: Decimal = Field(..., description="Execution price")
    qty: Decimal = Field(..., description="Quantity traded")

    resulting_pair_cost: Decimal = Field(..., description="Pair cost after this trade")
    resulting_delta: Decimal = Field(..., description="Position delta after this trade")

    order_id: Optional[str] = Field(None, description="Order ID from exchange")
    market_id: str = Field(..., description="Market identifier")

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class MarketInfo(BaseModel):
    """Information about a Polymarket market."""

    market_id: str = Field(..., description="Market identifier")
    condition_id: str = Field(..., description="Condition ID for the market")

    token_id_yes: str = Field(..., description="Token ID for YES outcome")
    token_id_no: str = Field(..., description="Token ID for NO outcome")

    question: str = Field(..., description="Market question")
    description: Optional[str] = Field(None, description="Market description")

    strike_price: Optional[Decimal] = Field(None, description="Strike price for price markets")
    expiration: datetime = Field(..., description="Market expiration time")

    active: bool = Field(default=True, description="Whether market is active")
    closed: bool = Field(default=False, description="Whether market is closed")

    min_tick_size: Decimal = Field(default=Decimal("0.01"), description="Minimum tick size")
    min_size: Decimal = Field(default=Decimal("1"), description="Minimum order size")

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

    def time_to_expiration(self) -> float:
        """Get seconds until expiration."""
        delta = self.expiration - datetime.utcnow()
        return max(0.0, delta.total_seconds())

    def is_within_settlement_buffer(self, buffer_seconds: int) -> bool:
        """Check if market is within settlement buffer."""
        return self.time_to_expiration() <= buffer_seconds


class TradingState(BaseModel):
    """Overall trading state."""

    position: Position = Field(default_factory=Position)
    market: Optional[MarketInfo] = Field(None, description="Current market")
    order_book: Optional[OrderBook] = Field(None, description="Current order book")

    is_halted: bool = Field(default=False, description="Trading halted flag")
    is_accumulating: bool = Field(default=False, description="Currently accumulating flag")

    last_trade_time: Optional[datetime] = Field(None, description="Last trade timestamp")
    total_trades: int = Field(default=0, description="Total number of trades")

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class RiskMetrics(BaseModel):
    """Risk metrics for monitoring."""

    current_delta: Decimal = Field(..., description="Current position delta")
    max_delta: Decimal = Field(..., description="Maximum allowed delta")

    pair_cost: Decimal = Field(..., description="Current pair cost")
    locked_profit: Decimal = Field(..., description="Locked profit amount")

    unrealized_pnl: Decimal = Field(default=Decimal("0"), description="Unrealized P&L")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="Realized P&L")

    time_to_settlement: float = Field(..., description="Seconds to settlement")
    liquidity_depth_yes: Decimal = Field(..., description="YES side liquidity")
    liquidity_depth_no: Decimal = Field(..., description="NO side liquidity")

    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(default="LOW")

    class Config:
        json_encoders = {
            Decimal: str
        }
