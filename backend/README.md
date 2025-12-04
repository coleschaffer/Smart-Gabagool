# Gabagool - Polymarket Volatility Arbitrage Bot

A production-grade automated trading bot for executing volatility arbitrage on Polymarket's 15-minute BTC/ETH price prediction markets.

## Strategy Overview

The bot exploits temporary price inefficiencies in binary prediction markets by accumulating paired YES/NO positions when the combined cost is below $1.00 (minus target profit margin). At settlement, paired positions always resolve to exactly $1.00, locking in guaranteed profit.

### Core Algorithm: "Accumulator"

Continuously scans order books looking for opportunities where:
- `Ask_YES + avg_NO < 0.98` (or target profit margin)
- `Ask_NO + avg_YES < 0.98`

When found, executes limit orders (post-only) while maintaining risk constraints.

### Rebalancing: "Equalizer"

Monitors position delta (qty_YES - qty_NO) and aggressively rebalances to minimize unhedged exposure.

### Risk Management: "Risk Engine"

- **Max Delta Constraint**: Limits unhedged position to 50 shares (configurable)
- **Liquidity Depth Check**: Requires 3x liquidity on opposite side before trading
- **Stop-Loss**: Emergency liquidation if mark-to-market loss exceeds 2%
- **Settlement Buffer**: Ceases accumulation at T-2 minutes

## Project Structure

```
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── position.py          # Pydantic models for positions, trades, order books
│   ├── core/
│   │   ├── __init__.py
│   │   ├── state_manager.py     # Redis-backed state persistence
│   │   ├── accumulator.py       # Main arbitrage algorithm
│   │   ├── equalizer.py         # Position rebalancing
│   │   └── risk_engine.py       # Risk monitoring and emergency liquidation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── polymarket_client.py # Polymarket CLOB API client
│   │   └── dashboard_api.py     # FastAPI dashboard endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── trading_service.py   # Main orchestrator
│   ├── config.py                # Configuration management
│   └── main.py                  # Entry point
├── logs/                        # Application logs
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Prerequisites

- Python 3.10+
- Redis 5.0+
- Polymarket API credentials
- Ethereum private key (for order signing)

### Setup

1. **Clone and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Start Redis:**
   ```bash
   redis-server
   ```

6. **Run the bot:**
   ```bash
   python -m src.main
   ```

## Configuration

Edit `.env` file with your settings:

### Required
- `POLYMARKET_API_KEY`: Your Polymarket API key
- `POLYMARKET_API_SECRET`: Your Polymarket API secret
- `PRIVATE_KEY`: Ethereum private key (without 0x prefix)

### Trading Parameters
- `MAX_UNHEDGED_DELTA=50`: Maximum unhedged position size
- `PROFIT_MARGIN=0.02`: Target profit (2% = pair cost < 0.98)
- `TRADE_SIZE=10`: Default trade size
- `SETTLEMENT_BUFFER_SECONDS=120`: Stop trading N seconds before settlement

### Risk Management
- `BAILOUT_STOP_LOSS_PERCENT=2.0`: Emergency liquidation threshold
- `MIN_LIQUIDITY_MULTIPLIER=3.0`: Required liquidity depth multiplier

## Dashboard API

The bot exposes a REST API and WebSocket for monitoring and control.

### Endpoints

**GET /api/status**
```json
{
  "running": true,
  "halted": false,
  "market": {...},
  "position": {
    "qty_yes": "45",
    "qty_no": "42",
    "delta": "3",
    "pair_cost": "0.975",
    "locked_profit": "1.05"
  },
  "total_trades": 87,
  "risk_level": "LOW"
}
```

**GET /api/trades?limit=20**
```json
{
  "trades": [...],
  "total": 87
}
```

**GET /api/orderbook**
```json
{
  "order_book": {
    "yes_asks": [{price: "0.52", size: "100"}],
    "yes_bids": [{price: "0.51", size: "80"}],
    "no_asks": [{price: "0.46", size: "120"}],
    "no_bids": [{price: "0.45", size: "90"}]
  }
}
```

**GET /api/market**
```json
{
  "market_id": "...",
  "question": "Will BTC price be above $95,000 at 3:15 PM UTC?",
  "expiration": "2025-12-03T15:15:00Z",
  "strike_price": "95000"
}
```

**GET /api/metrics**
```json
{
  "metrics": {
    "current_delta": "3",
    "max_delta": "50",
    "locked_profit": "1.05",
    "unrealized_pnl": "0.15",
    "time_to_settlement": 127.5,
    "risk_level": "LOW"
  }
}
```

**POST /api/start**
Start trading service

**POST /api/halt**
Halt accumulation (stop opening new positions)

**POST /api/resume**
Resume accumulation

**POST /api/panic**
Emergency close all positions immediately

**WebSocket /ws/live**
Real-time updates every second

## Architecture

### Components

1. **PolymarketClient** (`src/api/polymarket_client.py`)
   - REST API wrapper for Polymarket CLOB
   - WebSocket streaming for real-time order books
   - Order signing with eth-account
   - Market filtering and discovery

2. **StateManager** (`src/core/state_manager.py`)
   - Redis-backed persistence
   - Atomic position updates
   - Trade history tracking
   - Metrics storage

3. **Accumulator** (`src/core/accumulator.py`)
   - Main trading loop (100ms interval)
   - Opportunity scanning
   - Constraint checking
   - Order execution

4. **Equalizer** (`src/core/equalizer.py`)
   - Delta monitoring
   - Aggressive rebalancing
   - Cost-aware bidding

5. **RiskEngine** (`src/core/risk_engine.py`)
   - Continuous risk monitoring
   - Stop-loss implementation
   - Emergency liquidation
   - Settlement buffer enforcement

6. **TradingService** (`src/services/trading_service.py`)
   - Main orchestrator
   - Market selection
   - Component coordination
   - Task monitoring

7. **Dashboard API** (`src/api/dashboard_api.py`)
   - FastAPI REST endpoints
   - WebSocket streaming
   - Monitoring and control

## Trading Flow

```
1. Start → Select 15-min BTC/ETH market
           ↓
2. Accumulator scans order book every 100ms
           ↓
3. Opportunity found: Ask_YES + avg_NO < 0.98
           ↓
4. Check constraints:
   - Delta < 50
   - Liquidity depth > 3x trade size
           ↓
5. Execute limit order (post-only)
           ↓
6. Update position atomically
           ↓
7. Equalizer monitors delta
           ↓
8. If delta != 0 → Rebalance
           ↓
9. Risk Engine checks:
   - Stop-loss
   - Settlement buffer
   - Liquidity
           ↓
10. At settlement → Paired positions = $1.00/share
```

## Monitoring

### Logs

Logs are written to:
- **Console**: INFO level (configurable via LOG_LEVEL)
- **File**: `logs/gabagool.log` (DEBUG level, includes all details)

### Redis Keys

- `gabagool:position` - Current position
- `gabagool:trades` - Trade history (sorted set)
- `gabagool:market` - Active market
- `gabagool:state` - Trading state
- `gabagool:metrics` - Performance metrics
- `gabagool:halt` - Halt flag

## Safety Features

1. **Post-Only Orders**: Avoids taker fees and ensures price discipline
2. **Atomic Updates**: Redis transactions prevent race conditions
3. **Delta Limits**: Constrains unhedged exposure
4. **Liquidity Checks**: Ensures exit liquidity exists
5. **Stop-Loss**: Auto-liquidate on adverse moves
6. **Settlement Buffer**: Stops accumulation before expiration
7. **Halt Flag**: Manual emergency stop
8. **Panic Button**: Immediate liquidation via API

## Performance Tuning

### Scan Interval
- Default: 100ms
- Faster = more responsive, higher CPU
- Slower = less CPU, may miss opportunities

### Trade Size
- Default: 10 shares
- Larger = faster accumulation, higher risk
- Smaller = slower accumulation, lower risk

### Max Delta
- Default: 50 shares
- Higher = more profit potential, higher risk
- Lower = less risk, slower accumulation

### Profit Margin
- Default: 2% (pair cost < 0.98)
- Higher = safer margins, fewer opportunities
- Lower = more opportunities, tighter margins

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Type checking
mypy src/

# Linting
pylint src/

# Formatting
black src/
```

### Debug Mode
```bash
LOG_LEVEL=DEBUG python -m src.main
```

## Troubleshooting

### "Cannot connect to Redis"
- Ensure Redis is running: `redis-server`
- Check REDIS_URL in `.env`

### "No suitable markets found"
- Check time of day (15-min markets may not always be available)
- Verify API credentials
- Check Polymarket website for active markets

### "Position delta exceeded"
- Equalizer will automatically rebalance
- Check `MAX_UNHEDGED_DELTA` setting
- Monitor order book liquidity

### "Emergency liquidation triggered"
- Stop-loss activated due to adverse price movement
- Review position and market conditions
- Adjust `BAILOUT_STOP_LOSS_PERCENT` if needed

## Security

- **Never commit `.env` file**
- Store private keys securely
- Use environment variables in production
- Enable firewall on dashboard port
- Use HTTPS in production
- Implement authentication for API endpoints

## License

MIT License - See LICENSE file for details

## Disclaimer

This software is for educational purposes only. Trading cryptocurrencies and prediction markets carries risk. Use at your own risk. The authors are not responsible for any financial losses.

## Support

For issues, questions, or contributions:
- GitHub Issues
- Email: support@gabagool.io
- Discord: [Join our server]

## Roadmap

- [ ] Multi-market support (trade multiple markets simultaneously)
- [ ] Advanced profit optimization (dynamic target margins)
- [ ] Machine learning for opportunity prediction
- [ ] Enhanced dashboard UI
- [ ] Backtesting framework
- [ ] Portfolio management
- [ ] Telegram alerts
