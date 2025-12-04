"""
Main entry point for Gabagool trading bot.
"""

import asyncio
import logging
import sys
from pathlib import Path

import uvicorn

from src.config import get_config
from src.api.dashboard_api import app

# Setup logging
def setup_logging():
    """Configure logging for the application."""
    config = get_config()

    # Create logs directory
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(detailed_formatter)

    # File handler
    file_handler = logging.FileHandler(log_dir / "gabagool.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    logging.info("Logging configured: level=%s", config.log_level)


def main():
    """Main entry point."""
    # Setup logging
    setup_logging()

    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Starting Gabagool Trading Bot")
    logger.info("=" * 60)

    # Load config
    config = get_config()

    # Log configuration (redact sensitive info)
    logger.info("Configuration:")
    logger.info("  API URL: %s", config.polymarket_api_url)
    logger.info("  Redis: %s", config.redis_url)
    logger.info("  Max Delta: %s", config.max_unhedged_delta)
    logger.info("  Profit Margin: %s", config.profit_margin)
    logger.info("  Trade Size: %s", config.trade_size)
    logger.info("  Settlement Buffer: %s seconds", config.settlement_buffer_seconds)
    logger.info("  Dashboard Port: %s", config.dashboard_port)

    # Validate configuration
    try:
        if not config.private_key:
            raise ValueError("PRIVATE_KEY not configured")

        if not config.polymarket_api_key:
            logger.warning("POLYMARKET_API_KEY not set - using unauthenticated mode")

        logger.info("Configuration validated")

    except Exception as e:
        logger.error("Configuration error: %s", e)
        logger.error("Please check your .env file")
        sys.exit(1)

    # Start FastAPI server
    logger.info("Starting dashboard API on port %s", config.dashboard_port)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.dashboard_port,
        log_level=config.log_level.lower(),
        access_log=False  # We handle logging ourselves
    )


if __name__ == "__main__":
    main()
