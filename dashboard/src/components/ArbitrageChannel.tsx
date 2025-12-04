'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { ArbitragePoint } from '@/types';

interface ArbitrageChannelProps {
  data: ArbitragePoint[];
}

export default function ArbitrageChannel({ data }: ArbitrageChannelProps) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const sumPrice = payload[0].value;
      const isBuyZone = sumPrice < 1.00;

      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
          <p className="text-gray-400 text-xs mb-1">{formatTime(label)}</p>
          <p className={`text-sm font-mono font-bold ${isBuyZone ? 'text-green-400' : 'text-yellow-400'}`}>
            Sum: ${sumPrice.toFixed(4)}
          </p>
          {isBuyZone && (
            <p className="text-xs text-green-400 mt-1">BUY ZONE</p>
          )}
        </div>
      );
    }
    return null;
  };

  // Add buy zone highlighting
  const dataWithZones = data.map(point => ({
    ...point,
    buyZone: point.sum_price < 1.00 ? point.sum_price : null,
    regularZone: point.sum_price >= 1.00 ? point.sum_price : null,
  }));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-xl h-full">
      <div className="mb-3">
        <h3 className="text-lg font-bold text-white">Arbitrage Channel</h3>
        <p className="text-sm text-gray-400">Buy when YES + NO &lt; $1.00 (green zone)</p>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={dataWithZones} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="buyZoneGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22C55E" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22C55E" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatTime}
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            domain={[0.95, 1.05]}
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
            label={{ value: 'Price Sum', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF' } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />

          {/* Reference line at 1.00 */}
          <ReferenceLine
            y={1.00}
            stroke="#F59E0B"
            strokeDasharray="5 5"
            strokeWidth={2}
            label={{
              value: 'Fair Value ($1.00)',
              position: 'right',
              fill: '#F59E0B',
              fontSize: 12,
            }}
          />

          {/* Buy zone (below 1.00) - highlighted in green */}
          <Line
            type="monotone"
            dataKey="buyZone"
            stroke="#22C55E"
            strokeWidth={3}
            dot={false}
            name="Buy Zone"
            animationDuration={300}
          />

          {/* Regular zone (above 1.00) */}
          <Line
            type="monotone"
            dataKey="regularZone"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={false}
            name="Regular"
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
