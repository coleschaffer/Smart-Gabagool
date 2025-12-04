# Gabagool Volatility Arbitrage Dashboard

Real-time trading dashboard for the Gabagool volatility arbitrage bot built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

### 1. Scoreboard
- **Current Market**: Displays the active market with YES/NO prices
- **Time Remaining**: Live countdown to market expiration
- **Current Pair Cost**: Real-time pair cost with color coding:
  - Green: < $0.99 (profitable)
  - Yellow: $0.99 - $1.00 (breakeven)
  - Red: > $1.00 (losing)
- **Locked Profit**: Risk-free profit from matched pairs
- **Delta Exposure**: Visual gauge showing YES vs NO balance

### 2. Charts

#### Accumulation Chart
- Tracks YES and NO share accumulation over time
- Green line: YES shares
- Red line: NO shares
- Goal: Lines should intertwine (balanced accumulation)

#### Exposure Chart
- "The Gap Chart" showing locked profit
- Red line: Total cost basis
- Blue line: Guaranteed payout (min of YES/NO)
- Shaded area: Locked profit

#### Arbitrage Channel
- Monitors YES + NO price sum
- Orange reference line at $1.00 (fair value)
- Green highlights when sum < $1.00 (buy zone)
- Blue when sum >= $1.00

#### Order Book
- Live market depth display
- YES and NO markets side-by-side
- Price levels with quantity visualization
- Spread calculation

### 3. Trade Ledger
- Last 20 executions in real-time
- Color-coded by side (Green=YES, Red=NO)
- Shows resulting pair cost after each trade
- Auto-scrolls to newest trades

### 4. Risk Status Indicators
- **Delta Status**: Safe/Warning/Danger based on position imbalance
- **Liquidity Status**: Market depth monitoring
- **API Connection**: Live connection status
- **Time Buffer**: Minutes remaining to settlement

### 5. Control Panel
- **Bot Status**: Active/Inactive indicator
- **Accumulation Status**: Running/Halted
- **Halt Button**: Stop new purchases (maintains positions)
- **Resume Button**: Resume accumulation
- **PANIC BUTTON**: Emergency close all positions with confirmation

## Technology Stack

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **Lucide React**: Icon library
- **Socket.io Client**: WebSocket real-time updates
- **React Query**: Data fetching and caching

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Update `.env.local` with your backend URL:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production

Build for production:
```bash
npm run build
```

Start production server:
```bash
npm start
```

## Backend API Requirements

The dashboard expects the following API endpoints:

### REST Endpoints
- `GET /api/status` - Bot status and current position
- `GET /api/trades?limit=20` - Recent trades
- `GET /api/orderbook` - Current order book
- `GET /api/market` - Market information
- `POST /api/panic` - Emergency close all positions
- `POST /api/halt` - Stop accumulation
- `POST /api/resume` - Resume accumulation
- `GET /api/history/accumulation` - Historical accumulation data
- `GET /api/history/exposure` - Historical exposure data
- `GET /api/history/arbitrage` - Historical arbitrage channel data

### WebSocket Endpoint
- `WS /ws` - Real-time updates

WebSocket message format:
```json
{
  "type": "trade" | "position" | "market" | "orderbook" | "status",
  "data": { ... }
}
```

## Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│                   HEADER + SCOREBOARD               │
├─────────────────────────────────────────────────────┤
│                  RISK STATUS INDICATORS             │
├──────────────────────────┬──────────────────────────┤
│  Accumulation Chart      │  Exposure Chart          │
├──────────────────────────┼──────────────────────────┤
│  Arbitrage Channel       │  Order Book              │
├─────────────────────────────────────────────────────┤
│                   TRADE LEDGER                      │
├─────────────────────────────────────────────────────┤
│                  CONTROL PANEL                      │
└─────────────────────────────────────────────────────┘
```

## Theme

Dark trading terminal aesthetic:
- Background: Dark gray/black (#030712)
- Text: White/light gray
- Profit: Green (#22C55E)
- Loss: Red (#EF4444)
- Warning: Yellow (#F59E0B)
- Info: Blue (#3B82F6)

## Data Refresh

- WebSocket: Real-time updates for trades, positions, market data
- Polling: Every 5 seconds as fallback
- Auto-reconnect: WebSocket reconnects automatically on disconnect

## Error Handling

- Failed API calls are caught and logged
- WebSocket disconnections trigger auto-reconnect
- Loading states shown during initial data fetch
- User-friendly error messages for control actions

## Performance

- Efficient re-renders with React hooks
- Chart data limited to recent history
- Trade ledger capped at 20 entries
- Smooth animations with CSS transitions

## Security Notes

- No sensitive credentials stored in frontend
- API calls proxied through Next.js
- CORS handled by backend
- WebSocket authentication (if implemented in backend)

## Customization

### Changing API URL
Update `NEXT_PUBLIC_API_URL` in `.env.local`

### Chart Time Windows
Modify data slicing in component files

### Color Thresholds
Adjust color logic in `Scoreboard.tsx` and other components

### Refresh Intervals
Update interval values in `page.tsx`

## Troubleshooting

### Dashboard shows "Disconnected"
- Check backend is running on correct port
- Verify WebSocket endpoint is accessible
- Check browser console for connection errors

### No data showing
- Verify API endpoints are returning data
- Check browser console for API errors
- Ensure CORS is configured on backend

### Charts not updating
- Check WebSocket connection status
- Verify message format matches expected structure
- Check browser console for parsing errors

## License

Proprietary - Gabagool Trading Systems

## Support

For issues or questions, contact the development team.
