#!/usr/bin/env python3
"""
Test script to verify all connections before running the bot.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import redis.asyncio as redis
from dotenv import load_dotenv

from src.config import get_config
from src.api.polymarket_client import PolymarketClient

# Load environment
load_dotenv()

async def test_redis():
    """Test Redis connection."""
    print("Testing Redis connection...")

    try:
        config = get_config()
        client = await redis.from_url(config.redis_url, decode_responses=True)

        # Test ping
        await client.ping()
        print("✓ Redis connection successful")

        # Test set/get
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        assert value == "test_value"
        await client.delete("test_key")
        print("✓ Redis read/write successful")

        await client.close()
        return True

    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False


async def test_polymarket():
    """Test Polymarket API connection."""
    print("\nTesting Polymarket API connection...")

    try:
        client = PolymarketClient()
        await client.connect()

        # Try to fetch markets
        markets = await client.get_markets(active=True)
        print(f"✓ Polymarket API connection successful")
        print(f"  Found {len(markets)} active markets")

        # Show a few markets
        if markets:
            print("\nSample markets:")
            for market in markets[:3]:
                print(f"  - {market.question}")

        await client.disconnect()
        return True

    except Exception as e:
        print(f"✗ Polymarket API connection failed: {e}")
        return False


async def test_config():
    """Test configuration."""
    print("\nTesting configuration...")

    try:
        config = get_config()

        # Check required fields
        checks = [
            ("Private key", bool(config.private_key)),
            ("API URL", bool(config.polymarket_api_url)),
            ("Redis URL", bool(config.redis_url)),
        ]

        all_ok = True
        for name, status in checks:
            symbol = "✓" if status else "✗"
            print(f"{symbol} {name}: {'configured' if status else 'MISSING'}")
            all_ok = all_ok and status

        # Show config (redacted)
        print("\nConfiguration:")
        print(f"  Max Delta: {config.max_unhedged_delta}")
        print(f"  Profit Margin: {config.profit_margin}")
        print(f"  Trade Size: {config.trade_size}")
        print(f"  Settlement Buffer: {config.settlement_buffer_seconds}s")
        print(f"  Dashboard Port: {config.dashboard_port}")

        return all_ok

    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Gabagool Trading Bot - Connection Test")
    print("=" * 60)
    print()

    results = []

    # Test config
    results.append(("Configuration", await test_config()))

    # Test Redis
    results.append(("Redis", await test_redis()))

    # Test Polymarket
    results.append(("Polymarket API", await test_polymarket()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        symbol = "✓" if passed else "✗"
        status = "PASSED" if passed else "FAILED"
        print(f"{symbol} {name}: {status}")
        all_passed = all_passed and passed

    print()

    if all_passed:
        print("✓ All tests passed! Ready to run the bot.")
        print("\nStart the bot with:")
        print("  ./run.sh")
        print("  or")
        print("  python -m src.main")
        return 0
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
