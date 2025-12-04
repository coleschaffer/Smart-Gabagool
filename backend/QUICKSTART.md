# Gabagool Quick Start Guide

Get the bot running in 5 minutes.

## Prerequisites

- Python 3.10+
- Redis installed
- Polymarket API credentials
- Ethereum private key

## Step 1: Install Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required settings:**
```bash
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_API_SECRET=your_api_secret_here
PRIVATE_KEY=your_ethereum_private_key_without_0x
```

**Recommended starting settings:**
```bash
MAX_UNHEDGED_DELTA=50
PROFIT_MARGIN=0.02
TRADE_SIZE=10
```

## Step 3: Start Redis

```bash
# In a new terminal
redis-server
```

## Step 4: Run the Bot

```bash
# Make run script executable
chmod +x run.sh

# Start the bot
./run.sh
```

Or manually:
```bash
python -m src.main
```

## Step 5: Access Dashboard

Open your browser:
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Quick API Test

```bash
# Get current status
curl http://localhost:8000/api/status

# Get recent trades
curl http://localhost:8000/api/trades?limit=10

# Get order book
curl http://localhost:8000/api/orderbook

# Start trading (if not auto-started)
curl -X POST http://localhost:8000/api/start

# Halt trading
curl -X POST http://localhost:8000/api/halt

# Resume trading
curl -X POST http://localhost:8000/api/resume
```

## Using Docker (Alternative)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f gabagool

# Stop
docker-compose down
```

## Monitoring

### View Logs
```bash
tail -f logs/gabagool.log
```

### Redis Data
```bash
# Connect to Redis
redis-cli

# View current position
GET gabagool:position

# View recent trades
ZREVRANGE gabagool:trades 0 9

# Check halt flag
GET gabagool:halt
```

### WebSocket Stream
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Position:', data.status.position);
    console.log('Risk Level:', data.status.risk_level);
};
```

## Trading Flow

1. **Bot starts** → Connects to Polymarket and Redis
2. **Market selection** → Finds 15-min BTC/ETH market
3. **Accumulation** → Scans for opportunities every 100ms
4. **Execution** → Places limit orders when profitable
5. **Rebalancing** → Equalizer reduces delta
6. **Risk monitoring** → Continuous safety checks
7. **Settlement** → Paired positions resolve to $1.00

## Emergency Controls

### Halt Trading (Stop New Positions)
```bash
curl -X POST http://localhost:8000/api/halt
```

### Emergency Close (Liquidate All)
```bash
curl -X POST http://localhost:8000/api/panic
```

### Stop Bot
```bash
# Press Ctrl+C in terminal
# Or via API:
curl -X POST http://localhost:8000/api/stop
```

## Common Issues

### "Cannot connect to Redis"
```bash
# Start Redis
redis-server
```

### "No suitable markets found"
- Check that 15-min markets are available on Polymarket
- Verify API credentials
- Check logs for errors

### "Private key validation failed"
- Ensure private key is 64 hex characters
- Remove "0x" prefix if present
- Check for extra whitespace

### "Permission denied: ./run.sh"
```bash
chmod +x run.sh
```

## Key Metrics to Watch

1. **Pair Cost**: Should be < 0.98 (for 2% profit margin)
2. **Delta**: Should stay near 0 (Equalizer manages this)
3. **Locked Profit**: Increases with each paired position
4. **Risk Level**: Should be LOW or MEDIUM
5. **Time to Settlement**: Bot stops at T-2 minutes

## Safety Features

- Post-only orders (maker rebates, no taker fees)
- Delta limit (default: 50 shares)
- Liquidity checks (3x trade size)
- Stop-loss (2% threshold)
- Settlement buffer (120 seconds)
- Manual halt flag
- Emergency liquidation

## Next Steps

1. Monitor the first few trades carefully
2. Adjust `TRADE_SIZE` based on your capital
3. Fine-tune `PROFIT_MARGIN` based on market conditions
4. Set up monitoring/alerts
5. Review logs regularly

## Support

- Documentation: `README.md`
- API Docs: http://localhost:8000/docs
- Logs: `logs/gabagool.log`

## Warning

**This bot trades with real money. Start with small position sizes and monitor closely.**

Good luck, and may the arbitrage be ever in your favor!
