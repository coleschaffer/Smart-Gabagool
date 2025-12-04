#!/usr/bin/env python3
"""
Utility script to view current position.
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.state_manager import StateManager


def format_decimal(value: Decimal, decimals: int = 4) -> str:
    """Format decimal for display."""
    return f"{value:.{decimals}f}"


async def main():
    """View current position."""
    state = StateManager()
    await state.connect()

    # Get position
    position = await state.get_position()

    # Get market
    market = await state.get_market()

    # Get recent trades
    trades = await state.get_recent_trades(5)

    # Get metrics
    metrics = await state.get_metrics()

    # Display
    print("=" * 60)
    print("Gabagool - Current Position")
    print("=" * 60)
    print()

    if market:
        print(f"Market: {market.question}")
        print(f"Expiration: {market.expiration}")
        print(f"Time remaining: {market.time_to_expiration():.1f} seconds")
        print()
    else:
        print("No active market")
        print()

    print("Position:")
    print(f"  YES: {format_decimal(position.qty_yes)} shares @ avg {format_decimal(position.avg_yes)}")
    print(f"       Total cost: ${format_decimal(position.cost_yes)}")
    print()
    print(f"  NO:  {format_decimal(position.qty_no)} shares @ avg {format_decimal(position.avg_no)}")
    print(f"       Total cost: ${format_decimal(position.cost_no)}")
    print()
    print(f"  Delta: {format_decimal(position.delta)} (unhedged)")
    print(f"  Pair Cost: ${format_decimal(position.pair_cost)}")
    print(f"  Locked Profit: ${format_decimal(position.locked_profit)}")
    print()

    paired_qty = min(position.qty_yes, position.qty_no)
    print(f"Paired Shares: {format_decimal(paired_qty)}")
    print(f"Value at Settlement: ${format_decimal(paired_qty)}")
    print()

    if trades:
        print("Recent Trades:")
        for trade in trades:
            print(f"  {trade.timestamp.strftime('%H:%M:%S')} | "
                  f"{trade.side:3s} | "
                  f"{format_decimal(trade.qty):>6s} @ {format_decimal(trade.price)} | "
                  f"Pair: {format_decimal(trade.resulting_pair_cost)} | "
                  f"Delta: {format_decimal(trade.resulting_delta):>6s}")
        print()

    if metrics:
        print("Metrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")

    await state.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
