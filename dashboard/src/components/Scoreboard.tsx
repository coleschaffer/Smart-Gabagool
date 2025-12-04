'use client';

import { useEffect, useState } from 'react';
import { MarketInfo, Position } from '@/types';
import { Clock, TrendingUp, DollarSign, Activity } from 'lucide-react';

interface ScoreboardProps {
  market: MarketInfo | null;
  position: Position | null;
}

export default function Scoreboard({ market, position }: ScoreboardProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>('');

  useEffect(() => {
    if (!market?.expiration_time) return;

    const updateTimer = () => {
      const now = new Date().getTime();
      const expiration = new Date(market.expiration_time).getTime();
      const diff = expiration - now;

      if (diff <= 0) {
        setTimeRemaining('EXPIRED');
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setTimeRemaining(`${hours}h ${minutes}m ${seconds}s`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [market?.expiration_time]);

  const getPairCostColor = (cost: number) => {
    if (cost < 0.99) return 'text-green-400';
    if (cost <= 1.00) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getDeltaPercentage = () => {
    if (!position) return 50;
    const total = position.yes_shares + position.no_shares;
    if (total === 0) return 50;
    return (position.yes_shares / total) * 100;
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 shadow-xl">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {/* Current Market */}
        <div className="md:col-span-2">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-blue-400" />
            <span className="text-gray-400 text-sm font-medium">CURRENT MARKET</span>
          </div>
          <div className="text-xl font-bold text-white truncate">
            {market?.market_title || 'Loading...'}
          </div>
          {market && (
            <div className="text-sm text-gray-400 mt-1">
              YES: ${market.yes_price.toFixed(3)} | NO: ${market.no_price.toFixed(3)}
            </div>
          )}
        </div>

        {/* Time Remaining */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-purple-400" />
            <span className="text-gray-400 text-sm font-medium">TIME REMAINING</span>
          </div>
          <div className="text-2xl font-mono font-bold text-white">
            {timeRemaining || '--:--:--'}
          </div>
        </div>

        {/* Current Pair Cost */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-orange-400" />
            <span className="text-gray-400 text-sm font-medium">PAIR COST</span>
          </div>
          <div className={`text-3xl font-mono font-bold ${getPairCostColor(position?.current_pair_cost || 1.0)}`}>
            ${(position?.current_pair_cost || 0).toFixed(4)}
          </div>
        </div>

        {/* Locked Profit */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-green-400" />
            <span className="text-gray-400 text-sm font-medium">LOCKED PROFIT</span>
          </div>
          <div className="text-3xl font-mono font-bold text-green-400">
            ${(position?.locked_profit || 0).toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {position?.locked_pairs || 0} pairs locked
          </div>
        </div>
      </div>

      {/* Delta Exposure Gauge */}
      <div className="mt-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-400 text-sm font-medium">DELTA EXPOSURE</span>
          <span className="text-gray-400 text-sm font-mono">
            YES: {position?.yes_shares || 0} | NO: {position?.no_shares || 0}
          </span>
        </div>
        <div className="relative w-full h-3 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-300"
            style={{ width: `${getDeltaPercentage()}%` }}
          />
          <div
            className="absolute top-0 right-0 h-full bg-gradient-to-l from-red-500 to-red-400 transition-all duration-300"
            style={{ width: `${100 - getDeltaPercentage()}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-green-400">YES</span>
          <span className="text-xs text-gray-400">
            Δ: {(position?.delta_exposure || 0).toFixed(2)}
          </span>
          <span className="text-xs text-red-400">NO</span>
        </div>
      </div>
    </div>
  );
}
