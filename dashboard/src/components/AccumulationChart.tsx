'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AccumulationPoint } from '@/types';

interface AccumulationChartProps {
  data: AccumulationPoint[];
}

export default function AccumulationChart({ data }: AccumulationChartProps) {
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
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
          <p className="text-gray-400 text-xs mb-1">{formatTime(label)}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className={`text-sm font-mono ${entry.dataKey === 'yes_shares' ? 'text-green-400' : 'text-red-400'}`}>
              {entry.name}: {entry.value.toFixed(2)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-xl h-full">
      <div className="mb-3">
        <h3 className="text-lg font-bold text-white">Accumulation Progress</h3>
        <p className="text-sm text-gray-400">Share accumulation over time (balanced = good)</p>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
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
            label={{ value: 'Shares', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF' } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="yes_shares"
            stroke="#22C55E"
            strokeWidth={2}
            dot={false}
            name="YES Shares"
            animationDuration={300}
          />
          <Line
            type="monotone"
            dataKey="no_shares"
            stroke="#EF4444"
            strokeWidth={2}
            dot={false}
            name="NO Shares"
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
