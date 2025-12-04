"""
Configuration management for Gabagool trading bot.
"""

import os
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""

    # Polymarket API
    polymarket_api_key: str = Field(..., env="POLYMARKET_API_KEY")
    polymarket_api_secret: str = Field(..., env="POLYMARKET_API_SECRET")
    polymarket_api_url: str = Field(
        default="https://clob.polymarket.com",
        env="POLYMARKET_API_URL"
    )

    # Ethereum
    private_key: str = Field(..., env="PRIVATE_KEY")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Trading Parameters
    max_unhedged_delta: Decimal = Field(
        default=Decimal("50"),
        env="MAX_UNHEDGED_DELTA"
    )
    profit_margin: Decimal = Field(
        default=Decimal("0.02"),
        env="PROFIT_MARGIN",
        description="Target profit margin (2%)"
    )
    settlement_buffer_seconds: int = Field(
        default=120,
        env="SETTLEMENT_BUFFER_SECONDS",
        description="Stop trading N seconds before settlement"
    )
    target_roi: Decimal = Field(
        default=Decimal("10.0"),
        env="TARGET_ROI",
        description="Target ROI percentage"
    )
    min_liquidity_multiplier: Decimal = Field(
        default=Decimal("3.0"),
        env="MIN_LIQUIDITY_MULTIPLIER",
        description="Require liquidity depth of N times trade size"
    )

    # Risk Management
    max_position_size: Decimal = Field(
        default=Decimal("1000"),
        env="MAX_POSITION_SIZE"
    )
    bailout_stop_loss_percent: Decimal = Field(
        default=Decimal("2.0"),
        env="BAILOUT_STOP_LOSS_PERCENT",
        description="Emergency liquidation threshold"
    )

    # Execution Settings
    trade_size: Decimal = Field(
        default=Decimal("10"),
        env="TRADE_SIZE",
        description="Default trade size"
    )
    scan_interval_ms: int = Field(
        default=100,
        env="SCAN_INTERVAL_MS",
        description="Market scan interval in milliseconds"
    )

    # Dashboard
    dashboard_port: int = Field(default=8000, env="DASHBOARD_PORT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        json_encoders = {
            Decimal: str
        }

    @validator("private_key")
    def validate_private_key(cls, v):
        """Ensure private key is properly formatted."""
        if not v:
            raise ValueError("PRIVATE_KEY is required")

        # Remove 0x prefix if present
        if v.startswith("0x"):
            v = v[2:]

        # Validate length
        if len(v) != 64:
            raise ValueError("PRIVATE_KEY must be 64 hex characters (32 bytes)")

        # Validate hex
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("PRIVATE_KEY must be valid hex")

        return v

    @validator("profit_margin", "target_roi")
    def validate_percentage(cls, v, field):
        """Ensure percentages are positive."""
        if v <= 0:
            raise ValueError(f"{field.name} must be positive")
        return v

    @validator("max_unhedged_delta", "max_position_size", "trade_size")
    def validate_positive(cls, v, field):
        """Ensure trading parameters are positive."""
        if v <= 0:
            raise ValueError(f"{field.name} must be positive")
        return v

    def get_scan_interval_seconds(self) -> float:
        """Get scan interval in seconds."""
        return self.scan_interval_ms / 1000.0

    def get_profit_target(self) -> Decimal:
        """Get target pair cost (1.00 - profit_margin)."""
        return Decimal("1.00") - self.profit_margin


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config

    if _config is None:
        _config = Config(
            polymarket_api_key=os.getenv("POLYMARKET_API_KEY", ""),
            polymarket_api_secret=os.getenv("POLYMARKET_API_SECRET", ""),
            polymarket_api_url=os.getenv("POLYMARKET_API_URL", "https://clob.polymarket.com"),
            private_key=os.getenv("PRIVATE_KEY", ""),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            max_unhedged_delta=Decimal(os.getenv("MAX_UNHEDGED_DELTA", "50")),
            profit_margin=Decimal(os.getenv("PROFIT_MARGIN", "0.02")),
            settlement_buffer_seconds=int(os.getenv("SETTLEMENT_BUFFER_SECONDS", "120")),
            target_roi=Decimal(os.getenv("TARGET_ROI", "10.0")),
            min_liquidity_multiplier=Decimal(os.getenv("MIN_LIQUIDITY_MULTIPLIER", "3.0")),
            max_position_size=Decimal(os.getenv("MAX_POSITION_SIZE", "1000")),
            bailout_stop_loss_percent=Decimal(os.getenv("BAILOUT_STOP_LOSS_PERCENT", "2.0")),
            trade_size=Decimal(os.getenv("TRADE_SIZE", "10")),
            scan_interval_ms=int(os.getenv("SCAN_INTERVAL_MS", "100")),
            dashboard_port=int(os.getenv("DASHBOARD_PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    return _config


def reload_config() -> Config:
    """Force reload configuration from environment."""
    global _config
    _config = None
    return get_config()
