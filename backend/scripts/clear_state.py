#!/usr/bin/env python3
"""
Utility script to clear all trading state from Redis.
WARNING: This will delete all position and trade history!
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.state_manager import StateManager


async def main():
    """Clear all state."""
    print("=" * 60)
    print("Gabagool - Clear State Utility")
    print("=" * 60)
    print()
    print("WARNING: This will delete ALL trading data:")
    print("  - Current position")
    print("  - Trade history")
    print("  - Market information")
    print("  - Metrics")
    print()

    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != "yes":
        print("Cancelled.")
        return

    print("\nClearing state...")

    state = StateManager()
    await state.connect()

    success = await state.clear_all()

    await state.disconnect()

    if success:
        print("✓ State cleared successfully")
    else:
        print("✗ Failed to clear state")


if __name__ == "__main__":
    asyncio.run(main())
