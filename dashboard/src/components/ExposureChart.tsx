'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ExposurePoint } from '@/types';

interface ExposureChartProps {
  data: ExposurePoint[];
}

export default function ExposureChart({ data }: ExposureChartProps) {
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
      const costBasis = payload.find((p: any) => p.dataKey === 'total_cost')?.value || 0;
      const guaranteedPayout = payload.find((p: any) => p.dataKey === 'guaranteed_payout')?.value || 0;
      const profit = guaranteedPayout - costBasis;

      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
          <p className="text-gray-400 text-xs mb-2">{formatTime(label)}</p>
          <p className="text-sm font-mono text-red-400">
            Cost: ${costBasis.toFixed(2)}
          </p>
          <p className="text-sm font-mono text-blue-400">
            Payout: ${guaranteedPayout.toFixed(2)}
          </p>
          <p className={`text-sm font-mono font-bold ${profit >= 0 ? 'text-green-400' : 'text-red-400'} mt-1 pt-1 border-t border-gray-700`}>
            Profit: ${profit.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-xl h-full">
      <div className="mb-3">
        <h3 className="text-lg font-bold text-white">Exposure & Profit</h3>
        <p className="text-sm text-gray-400">The gap between lines = locked profit</p>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <AreaChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
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
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
            label={{ value: 'USDC', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF' } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
          <Area
            type="monotone"
            dataKey="total_cost"
            stroke="#EF4444"
            fill="transparent"
            strokeWidth={2}
            name="Cost Basis"
            animationDuration={300}
          />
          <Area
            type="monotone"
            dataKey="guaranteed_payout"
            stroke="#3B82F6"
            fill="url(#profitGradient)"
            strokeWidth={2}
            name="Guaranteed Payout"
            animationDuration={300}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
