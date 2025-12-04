# 🍖 Gabagool - Polymarket Volatility Arbitrage Bot

**Gabagool** is an automated volatility arbitrage trading bot for Polymarket that exploits pricing inefficiencies in prediction markets. The bot monitors market volatility, identifies arbitrage opportunities, and executes delta-neutral trades to capture guaranteed profits while managing risk exposure.

## 🎯 Strategy Overview

The **Gabagool Strategy** combines several sophisticated trading techniques:

### 1. **Volatility Arbitrage**
- Monitors rapid price movements and volatility spikes
- Identifies markets with high vol/low liquidity where pricing breaks down
- Captures spread profits when markets mean-revert

### 2. **Delta-Neutral Hedging**
- Maintains market-neutral positions to eliminate directional risk
- Dynamically rebalances delta exposure as prices move
- Ensures profitability regardless of event outcome

### 3. **Cross-Market Arbitrage**
- Identifies pricing discrepancies between related markets
- Exploits correlated events with divergent pricing
- Captures risk-free profits from market inefficiencies

### 4. **Smart Order Routing**
- Splits large orders to minimize market impact
- Uses limit orders to capture better fills
- Implements anti-gaming measures against front-runners

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Gabagool System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │   Next.js    │      │   FastAPI    │      │  Redis   │ │
│  │  Dashboard   │◄────►│   Backend    │◄────►│  Cache   │ │
│  │  (Port 3000) │      │  (Port 8000) │      │ (Port    │ │
│  └──────────────┘      └──────────────┘      │  6379)   │ │
│         │                     │               └──────────┘ │
│         │                     │                            │
│         │                     ▼                            │
│         │              ┌──────────────┐                    │
│         │              │  Polymarket  │                    │
│         │              │   CLOB API   │                    │
│         │              └──────────────┘                    │
│         │                     │                            │
│         └─────────────────────┘                            │
│                                                             │
│  Components:                                                │
│  • Real-time market monitoring                             │
│  • Volatility tracking & scoring                           │
│  • Arbitrage opportunity detection                         │
│  • Delta-neutral position management                       │
│  • Risk exposure monitoring                                │
│  • Automated trade execution                               │
│  • Performance analytics                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

Before running Gabagool, ensure you have:

- **Docker Desktop** (v20.10+)
- **Docker Compose** (v2.0+)
- **Python** 3.11+ (for local development)
- **Node.js** 20+ (for local development)
- **Polymarket Account** with API credentials
- **Polygon Wallet** with USDC for trading
- **Minimum Capital**: $1,000+ USDC recommended

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd Smart-Gabagool

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required variables:
- `POLYMARKET_API_KEY`: Your Polymarket API key
- `POLYMARKET_API_SECRET`: Your Polymarket API secret
- `PRIVATE_KEY`: Your Polygon wallet private key

### 3. Start the System

```bash
# Start all services
make dev

# Or use the convenience script
./scripts/start-dev.sh
```

The dashboard will open at `http://localhost:3000`

### 4. Monitor & Trade

- **Dashboard**: View opportunities, positions, and performance
- **API Docs**: `http://localhost:8000/docs`
- **Logs**: `make logs`

## ⚙️ Configuration Options

### Risk Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_UNHEDGED_DELTA` | 100 | Maximum unhedged position size (USDC) |
| `PROFIT_MARGIN` | 0.02 | Minimum profit margin to execute trade (2%) |
| `SETTLEMENT_BUFFER_SECONDS` | 300 | Avoid markets settling within this time |
| `TARGET_ROI` | 0.05 | Target return on investment (5%) |
| `MAX_POSITION_SIZE` | 1000 | Maximum size per position (USDC) |
| `VOLATILITY_THRESHOLD` | 0.15 | Minimum volatility to trade (15%) |

### Advanced Settings

```python
# backend/config.py

# Order execution
ORDER_TIMEOUT = 30  # seconds
MAX_SLIPPAGE = 0.005  # 0.5%
USE_LIMIT_ORDERS = True

# Monitoring
POLL_INTERVAL = 5  # seconds
WEBSOCKET_RECONNECT = 10  # seconds

# Risk management
STOP_LOSS_ENABLED = True
MAX_DAILY_LOSS = 100  # USDC
CORRELATION_THRESHOLD = 0.7
```

## 📡 API Documentation

### Core Endpoints

#### Get Opportunities
```http
GET /api/opportunities
```
Returns current arbitrage opportunities with scores and parameters.

#### Get Positions
```http
GET /api/positions
```
Returns all active positions with delta, PnL, and hedge status.

#### Execute Trade
```http
POST /api/trade
Content-Type: application/json

{
  "market_id": "string",
  "side": "BUY|SELL",
  "size": 100,
  "price": 0.55
}
```

#### Get Metrics
```http
GET /api/metrics
```
Returns performance metrics, statistics, and health status.

### WebSocket Feeds

```javascript
// Real-time opportunities
ws://localhost:8000/ws/opportunities

// Position updates
ws://localhost:8000/ws/positions

// Market data
ws://localhost:8000/ws/markets
```

## 🎮 Makefile Commands

```bash
make dev        # Start all services in development mode
make backend    # Start only backend service
make dashboard  # Start only dashboard service
make redis      # Start only Redis service
make logs       # View logs from all services
make logs-backend   # View backend logs only
make logs-dashboard # View dashboard logs only
make clean      # Stop and remove all containers
make reset      # Clean and remove volumes
make test       # Run test suite
make build      # Rebuild all images
make shell-backend  # Open shell in backend container
make shell-dashboard # Open shell in dashboard container
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run backend tests only
cd backend && pytest

# Run with coverage
cd backend && pytest --cov=. --cov-report=html

# Run specific test
cd backend && pytest tests/test_arbitrage.py -v
```

## 📊 Strategy Deep Dive

### Opportunity Scoring

The bot uses a multi-factor scoring system:

```python
score = (
    volatility_score * 0.3 +      # Price volatility
    spread_score * 0.25 +          # Bid-ask spread
    volume_score * 0.2 +           # Trading volume
    correlation_score * 0.15 +     # Cross-market correlation
    settlement_score * 0.1         # Time to settlement
)
```

**Minimum Score to Trade**: 7.0/10

### Position Management

1. **Entry**: Execute when score > threshold and profit margin met
2. **Monitoring**: Track delta exposure in real-time
3. **Rebalancing**: Hedge when delta exceeds threshold
4. **Exit**: Close when profit target hit or risk increases

### Risk Controls

- **Position Limits**: Max size per market and total exposure
- **Delta Limits**: Maximum unhedged directional exposure
- **Correlation Limits**: Max exposure to correlated markets
- **Time Limits**: Avoid markets close to settlement
- **Loss Limits**: Daily loss limits with circuit breakers

## ⚠️ Risk Warnings

### Critical Risks

1. **Smart Contract Risk**: Polymarket contracts could have bugs
2. **Market Risk**: Prices can move against positions
3. **Liquidity Risk**: May not be able to exit positions
4. **Execution Risk**: Slippage and failed transactions
5. **Oracle Risk**: Settlement depends on UMA oracle
6. **Gas Risk**: High Polygon fees during congestion

### Best Practices

- Start with small position sizes
- Monitor positions constantly
- Keep sufficient USDC for hedging
- Test with paper trading first
- Never risk more than you can afford to lose
- Keep private keys secure
- Monitor gas prices
- Have exit strategies for all positions

### Loss Scenarios

Even with arbitrage, you can lose money:
- Failed hedges due to liquidity issues
- Rapid price movements preventing rebalancing
- Smart contract exploits or bugs
- Oracle manipulation or failures
- Gas price spikes making trades unprofitable

## 🔐 Security

### API Key Management

- Never commit `.env` file
- Use environment variables in production
- Rotate API keys regularly
- Limit API key permissions

### Wallet Security

- Use a dedicated trading wallet
- Never share private keys
- Keep majority of funds in cold storage
- Monitor for unauthorized transactions

### System Security

- Run on secure infrastructure
- Use HTTPS in production
- Implement rate limiting
- Monitor for anomalies
- Keep dependencies updated

## 📈 Performance Monitoring

### Key Metrics

- **Total PnL**: Cumulative profit/loss
- **Win Rate**: Percentage of profitable trades
- **Average ROI**: Return per trade
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Delta Exposure**: Current directional risk

### Alerts

Configure alerts for:
- Large unhedged positions
- Failed hedge attempts
- API errors or disconnections
- Unusual price movements
- Settlement events

## 🛠️ Troubleshooting

### Common Issues

**Docker not starting**
```bash
# Check Docker is running
docker ps

# Restart Docker Desktop
# Check logs: make logs
```

**Backend can't connect to Redis**
```bash
# Check Redis is healthy
docker ps | grep redis

# Restart Redis
docker-compose restart redis
```

**API authentication errors**
```bash
# Verify .env credentials
cat .env | grep API_KEY

# Check Polymarket API status
curl https://clob.polymarket.com/ping
```

**Out of gas errors**
```bash
# Check Polygon balance
# Fund wallet with MATIC for gas
# Adjust gas price settings
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Start with debug
docker-compose up --build
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is for educational purposes. Trading cryptocurrencies involves substantial risk of loss. Use at your own risk.

## 🙏 Acknowledgments

- Polymarket CLOB API
- FastAPI framework
- Next.js framework
- Redis for caching
- The DeFi community

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` folder
- **API Docs**: `http://localhost:8000/docs`

---

**Disclaimer**: This software is provided "as is" without warranty. Trading involves risk of loss. Never trade with funds you cannot afford to lose. Past performance does not guarantee future results.
