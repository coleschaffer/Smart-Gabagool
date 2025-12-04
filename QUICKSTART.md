# Gabagool - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Clone & Setup
```bash
cd /Users/coleschaffer/Desktop/Smart-Gabagool
./scripts/setup.sh
```

### Step 2: Configure Credentials
```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required:**
- `POLYMARKET_API_KEY` - From https://polymarket.com/settings/api
- `POLYMARKET_API_SECRET` - From Polymarket
- `PRIVATE_KEY` - Your Polygon wallet (without 0x)

### Step 3: Start
```bash
./scripts/start-dev.sh
# OR
make dev
```

### Step 4: Access
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 📋 Essential Commands

```bash
# Start services
make dev              # Start with logs
make dev-d            # Start in background

# View logs
make logs             # All services
make logs-backend     # Backend only
make logs-dashboard   # Dashboard only

# Stop
make stop             # Stop services
make clean            # Stop and remove

# Status
make ps               # Service status
make stats            # Resource usage

# Shell access
make shell-backend    # Backend shell
make shell-dashboard  # Dashboard shell
make shell-redis      # Redis CLI

# Testing
make test             # Run tests
```

## 🎯 First Time Checklist

- [ ] Docker Desktop installed and running
- [ ] `.env` file created and configured
- [ ] Polymarket API credentials added
- [ ] Wallet private key added
- [ ] Sufficient USDC in wallet
- [ ] Services started successfully
- [ ] Dashboard accessible at localhost:3000
- [ ] Backend health check passing

## ⚡ Common Tasks

### Check if Everything is Running
```bash
make ps
# Should show all services as "Up"
```

### View Real-Time Logs
```bash
make logs
# Ctrl+C to exit (services keep running)
```

### Restart After Code Changes
```bash
# Auto-reload is enabled, no restart needed!
# If you change dependencies:
make build
make dev
```

### Stop Everything
```bash
make stop     # Stop but keep containers
make clean    # Stop and remove containers
```

## 🐛 Quick Troubleshooting

### "Port already in use"
```bash
# Find and kill process
lsof -i :3000  # or :8000, :6379
kill -9 <PID>
```

### "Docker daemon not running"
```bash
# Start Docker Desktop, then:
make dev
```

### ".env not configured"
```bash
nano .env
# Add real credentials, then:
make dev
```

### "Backend won't start"
```bash
make logs-backend  # Check error
make build-backend # Rebuild
make dev          # Restart
```

## 📊 Monitoring

### Dashboard Features
- Real-time opportunities
- Active positions & PnL
- Risk exposure metrics
- Trade execution interface
- Performance analytics

### API Endpoints
- `GET /health` - Health check
- `GET /api/opportunities` - Current opportunities
- `GET /api/positions` - Active positions
- `GET /api/metrics` - Performance metrics
- `POST /api/trade` - Execute trade

### WebSocket Feeds
- `ws://localhost:8000/ws/opportunities` - Live opportunities
- `ws://localhost:8000/ws/positions` - Position updates
- `ws://localhost:8000/ws/markets` - Market data

## ⚠️ Safety Reminders

1. **Start Small**: Begin with minimum position sizes
2. **Monitor Constantly**: Keep dashboard open while trading
3. **Check Delta**: Watch unhedged exposure in real-time
4. **Have USDC**: Keep funds available for hedging
5. **Paper Trade**: Test strategies before risking capital
6. **Risk Only What You Can Lose**: Trading involves loss risk

## 🔐 Security Checklist

- [ ] `.env` file NOT committed to git
- [ ] Private key stored securely
- [ ] API keys have minimum required permissions
- [ ] Using dedicated trading wallet
- [ ] Majority of funds in cold storage
- [ ] Regular monitoring for unauthorized access

## 📈 Next Steps

1. **Test Connection**: Check dashboard shows market data
2. **Monitor Opportunities**: Watch scoring in real-time
3. **Start Small**: Execute first trades with minimal size
4. **Track Performance**: Monitor PnL and metrics
5. **Scale Up**: Gradually increase size as comfortable
6. **Optimize**: Tune parameters in `.env`

## 🆘 Get Help

- **Documentation**: `cat README.md`
- **Docker Guide**: `cat DOCKER_SETUP.md`
- **Commands**: `make help`
- **Logs**: `make logs`
- **API Docs**: http://localhost:8000/docs

## 💡 Pro Tips

1. **Keep Logs Open**: Run `make logs` in separate terminal
2. **Use Makefile**: Faster than docker-compose commands
3. **Monitor Resources**: Check `make stats` periodically
4. **Backup Redis**: Run `make backup-redis` before updates
5. **Test Changes**: Use paper trading mode first

---

## 🎮 Command Cheat Sheet

| Command | What It Does |
|---------|-------------|
| `make dev` | Start everything |
| `make stop` | Stop everything |
| `make logs` | View all logs |
| `make ps` | Check status |
| `make clean` | Clean up |
| `make test` | Run tests |
| `make help` | See all commands |

---

**Ready to trade?** Run `make dev` and open http://localhost:3000

**Need help?** Check logs with `make logs` or read `README.md`

**Found a bug?** Create an issue with logs and steps to reproduce
