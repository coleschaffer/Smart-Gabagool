# Docker Setup Guide

## Quick Start

```bash
# 1. Run setup script
./scripts/setup.sh

# 2. Configure environment
nano .env

# 3. Start development environment
./scripts/start-dev.sh

# Or use Makefile
make setup
make dev
```

## Project Structure

```
Smart-Gabagool/
├── docker-compose.yml          # Multi-container orchestration
├── Makefile                    # Convenient commands
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # Main documentation
├── DOCKER_SETUP.md           # This file
│
├── backend/
│   ├── Dockerfile            # Python backend image
│   ├── requirements.txt      # Python dependencies
│   ├── main.py              # FastAPI application
│   └── ...                   # Application code
│
├── dashboard/
│   ├── Dockerfile            # Node.js frontend image
│   ├── package.json         # Node dependencies
│   ├── next.config.js       # Next.js configuration
│   └── ...                   # Frontend code
│
└── scripts/
    ├── setup.sh             # Initial setup script
    └── start-dev.sh         # Development startup script
```

## Docker Services

### 1. Redis (Cache & State)
- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: redis-data (persistent)
- **Purpose**: Caching market data, storing state

### 2. Backend (FastAPI)
- **Base**: python:3.11-slim
- **Port**: 8000
- **Volume**: ./backend (hot-reload)
- **Purpose**: Trading logic, API endpoints, WebSocket

### 3. Dashboard (Next.js)
- **Base**: node:20-alpine
- **Port**: 3000
- **Volume**: ./dashboard (hot-reload)
- **Purpose**: Web UI, real-time monitoring

## Environment Variables

### Required
- `POLYMARKET_API_KEY` - Your Polymarket API key
- `POLYMARKET_API_SECRET` - Your Polymarket API secret
- `PRIVATE_KEY` - Your Polygon wallet private key

### Optional (with defaults)
- `REDIS_URL=redis://redis:6379`
- `MAX_UNHEDGED_DELTA=100`
- `PROFIT_MARGIN=0.02`
- `SETTLEMENT_BUFFER_SECONDS=300`
- `TARGET_ROI=0.05`

See `.env.example` for full list with descriptions.

## Makefile Commands

### Development
```bash
make dev          # Start all services
make dev-d        # Start in background
make stop         # Stop all services
make restart      # Restart services
make logs         # View all logs
make logs-backend # View backend logs only
make logs-dashboard # View dashboard logs only
```

### Management
```bash
make ps           # Show service status
make stats        # Show resource usage
make clean        # Stop and remove containers
make reset        # Remove volumes (WARNING: deletes data)
```

### Building
```bash
make build        # Rebuild all images
make build-backend # Rebuild backend only
make build-dashboard # Rebuild dashboard only
```

### Testing
```bash
make test         # Run all tests
make test-backend # Run backend tests
make test-coverage # Run with coverage
```

### Utilities
```bash
make shell-backend   # Open backend shell
make shell-dashboard # Open dashboard shell
make shell-redis     # Open Redis CLI
make check-env       # Verify .env configuration
make setup           # Initial setup
```

## Docker Compose Details

### Service Dependencies
```
dashboard → backend → redis
```
Services start in order, waiting for health checks.

### Health Checks
- **Redis**: `redis-cli ping` every 10s
- **Backend**: HTTP GET to `/health` every 30s
- **Dashboard**: HTTP GET to `/api/health` every 30s

### Networking
All services connected via `gabagool-network` bridge network.
Services can reach each other by name (e.g., `redis`, `backend`).

### Volumes
- **redis-data**: Persistent Redis data
- **./backend**: Hot-reload for backend code
- **./dashboard**: Hot-reload for dashboard code
- Anonymous volumes for node_modules and .next to avoid conflicts

## Development Workflow

### 1. Initial Setup
```bash
# Clone repo
git clone <repo-url>
cd Smart-Gabagool

# Run setup
./scripts/setup.sh

# Configure
nano .env
```

### 2. Start Development
```bash
# Start all services
./scripts/start-dev.sh

# Or with Makefile
make dev
```

### 3. Make Changes
- Backend: Edit files in `./backend` - auto-reloads
- Dashboard: Edit files in `./dashboard` - auto-reloads
- No need to rebuild unless changing dependencies

### 4. View Logs
```bash
# All services
make logs

# Specific service
make logs-backend
make logs-dashboard
```

### 5. Access Services
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379

### 6. Stop Services
```bash
# Stop (containers remain)
make stop

# Stop and remove
make clean
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :3000  # or :8000, :6379

# Kill process or change ports in docker-compose.yml
```

### Container Won't Start
```bash
# Check logs
make logs

# Rebuild image
make build

# Clean and restart
make clean
make dev
```

### Permission Errors
```bash
# On Linux, add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
```

### Redis Connection Errors
```bash
# Check Redis is running
docker ps | grep redis

# Restart Redis
docker-compose restart redis

# Check connection
docker-compose exec redis redis-cli ping
```

### Backend Can't Find Modules
```bash
# Rebuild backend image
make build-backend

# Check requirements.txt is correct
cat backend/requirements.txt

# Check Python version in Dockerfile
```

### Dashboard Build Fails
```bash
# Clear Next.js cache
rm -rf dashboard/.next

# Rebuild
make build-dashboard

# Check Node version in Dockerfile
```

### Out of Disk Space
```bash
# Remove unused images
docker system prune -a

# Check disk usage
docker system df

# Remove old volumes
docker volume prune
```

## Production Deployment

### Build Production Images
```bash
# Edit docker-compose.prod.yml
# Change to production Dockerfile targets

# Build
docker-compose -f docker-compose.prod.yml build

# Push to registry
docker-compose -f docker-compose.prod.yml push
```

### Environment Variables
- Use secrets management (AWS Secrets Manager, etc.)
- Never commit production credentials
- Use separate .env for production

### Security
- Run containers as non-root user
- Use HTTPS/TLS in production
- Implement rate limiting
- Enable authentication
- Monitor for vulnerabilities

### Scaling
```bash
# Scale services
docker-compose up -d --scale backend=3

# Use load balancer (nginx, traefik)
# Consider Kubernetes for production
```

## Advanced Configuration

### Custom Network
```yaml
networks:
  gabagool-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Resource Limits
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 512M
```

### Logging
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Override File
Create `docker-compose.override.yml` for local customizations:
```yaml
version: '3.8'
services:
  backend:
    environment:
      - DEBUG=true
    ports:
      - "5678:5678"  # Debugger port
```

## Monitoring

### Container Stats
```bash
# Real-time stats
docker stats

# Or with make
make stats
```

### Health Status
```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose ps backend
```

### Logs Analysis
```bash
# Follow all logs
make logs

# Filter logs
docker-compose logs backend | grep ERROR

# Last 100 lines
docker-compose logs --tail=100 backend
```

## Backup & Restore

### Backup Redis Data
```bash
# Create backup
docker-compose exec redis redis-cli BGSAVE

# Copy data
docker cp gabagool-redis:/data/dump.rdb ./backup/
```

### Restore Redis Data
```bash
# Stop Redis
docker-compose stop redis

# Replace data
docker cp ./backup/dump.rdb gabagool-redis:/data/

# Start Redis
docker-compose start redis
```

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Redis Documentation](https://redis.io/documentation)

## Support

For issues:
1. Check logs: `make logs`
2. Review troubleshooting section
3. Search GitHub issues
4. Create new issue with logs and steps to reproduce

---

**Note**: This is a development setup. Production deployments require additional security, monitoring, and scaling considerations.
