# Quick Start Guide - Gabagool Dashboard

## Prerequisites
- Node.js 18+ installed
- Backend API running on port 8000
- Terminal/command line access

## 5-Minute Setup

### Step 1: Navigate to Directory
```bash
cd /Users/coleschaffer/Desktop/Smart-Gabagool/dashboard
```

### Step 2: Install Dependencies (First Time Only)
```bash
npm install
```

### Step 3: Configure Environment (First Time Only)
```bash
cp .env.local.example .env.local
```

Edit `.env.local` if your backend is not on `http://localhost:8000`:
```env
NEXT_PUBLIC_API_URL=http://your-backend-url:port
```

### Step 4: Start Dashboard
```bash
npm run dev
```

OR use the start script:
```bash
./start.sh
```

### Step 5: Open Browser
Navigate to: **http://localhost:3000**

## That's It!

Your dashboard should now be running and connecting to the backend.

## What You Should See

1. **Scoreboard** at top with current market info
2. **Risk Status Indicators** showing connection status
3. **Four Charts** displaying real-time data
4. **Trade Ledger** showing recent executions
5. **Control Panel** at bottom with override controls

## Common Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

## Troubleshooting

### "Cannot connect to backend"
✅ **Solution**: Make sure backend is running on port 8000
```bash
curl http://localhost:8000/api/status
```

### "Module not found" errors
✅ **Solution**: Reinstall dependencies
```bash
rm -rf node_modules .next
npm install
```

### Port 3000 already in use
✅ **Solution**: Kill existing process or use different port
```bash
# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or run on different port
PORT=3001 npm run dev
```

### Dashboard shows "Disconnected"
✅ **Solution**: Check WebSocket connection
- Verify backend WebSocket endpoint is accessible
- Check browser console for connection errors
- Ensure no firewall blocking WebSocket

## File Locations

- **Main Page**: `src/app/page.tsx`
- **Components**: `src/components/*.tsx`
- **API Client**: `src/lib/api.ts`
- **Types**: `src/types/index.ts`
- **Styles**: `src/app/globals.css`
- **Config**: `next.config.js`, `.env.local`

## Dashboard Features Quick Reference

### Scoreboard (Top)
- Current market name and prices
- Countdown to expiration
- Real-time pair cost (color-coded)
- Locked profit display
- Position balance gauge

### Charts (Middle)
1. **Accumulation**: YES/NO share growth
2. **Exposure**: Locked profit visualization
3. **Arbitrage**: Price efficiency monitoring
4. **Order Book**: Live market depth

### Trade Ledger
- Last 20 trades
- Timestamp, side, price, quantity
- Resulting pair cost per trade

### Control Panel (Bottom)
- Bot status indicator
- Halt/Resume accumulation
- PANIC button (emergency close)

### Risk Indicators
- Delta: Position balance status
- Liquidity: Market depth status
- API: Connection status
- Buffer: Time to settlement

## Keyboard Shortcuts

None currently - all controls via mouse/touch

## Need Help?

1. Check `README.md` for detailed documentation
2. Check `PROJECT_SUMMARY.md` for architecture details
3. Check browser console (F12) for error messages
4. Check backend logs for API issues

## Production Deployment

### Docker
```bash
# Build production image
docker build -t gabagool-dashboard:latest .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://your-backend:8000 \
  gabagool-dashboard:latest
```

### Docker Compose
```bash
# Update docker-compose.yml with backend details
docker-compose up -d
```

## Environment Variables

### Required
- `NEXT_PUBLIC_API_URL` - Backend API base URL

### Optional
- `NEXT_PUBLIC_WS_URL` - WebSocket URL (defaults to API_URL with ws://)
- `PORT` - Server port (default: 3000)
- `NODE_ENV` - Environment (development/production)

## Security Notes

- Never commit `.env.local` to git
- Backend should handle all authentication
- Use HTTPS in production
- Enable CORS properly on backend
- Rate limit API endpoints

## Next Steps

1. Verify backend is running and accessible
2. Check WebSocket connection in dashboard
3. Monitor for real-time updates
4. Test control panel actions
5. Review all charts for data

## Support

For issues:
1. Check browser console for errors
2. Verify backend is responsive
3. Check network tab for failed requests
4. Review backend logs

---

**Dashboard Version**: 1.0.0
**Last Updated**: December 2024
**Built with**: Next.js 14 + TypeScript + Tailwind CSS
