'use client';

import { useEffect, useRef } from 'react';
import { Trade } from '@/types';
import { ArrowUp, ArrowDown } from 'lucide-react';

interface TradeLedgerProps {
  trades: Trade[];
}

export default function TradeLedger({ trades }: TradeLedgerProps) {
  const tableRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to newest trade
    if (tableRef.current) {
      tableRef.current.scrollTop = 0;
    }
  }, [trades]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const getPairCostColor = (cost: number) => {
    if (cost < 0.99) return 'text-green-400';
    if (cost <= 1.00) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800">
        <h3 className="text-lg font-bold text-white">Trade Ledger</h3>
        <p className="text-sm text-gray-400">Recent executions (newest first)</p>
      </div>
      <div ref={tableRef} className="overflow-y-auto max-h-96">
        <table className="w-full">
          <thead className="bg-gray-800 sticky top-0 z-10">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Time
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Side
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Price
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Qty
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Cost
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Pair Cost
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {trades.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No trades yet
                </td>
              </tr>
            ) : (
              trades.map((trade) => (
                <tr
                  key={trade.id}
                  className="hover:bg-gray-800 transition-colors duration-150"
                >
                  <td className="px-4 py-3 text-sm text-gray-300 font-mono">
                    {formatTime(trade.timestamp)}
                  </td>
                  <td className="px-4 py-3">
                    <div className={`flex items-center gap-1 font-semibold ${
                      trade.side === 'YES' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {trade.side === 'YES' ? (
                        <ArrowUp className="w-4 h-4" />
                      ) : (
                        <ArrowDown className="w-4 h-4" />
                      )}
                      <span>{trade.side}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300 font-mono text-right">
                    ${trade.price.toFixed(4)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300 font-mono text-right">
                    {trade.quantity.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300 font-mono text-right">
                    ${trade.cost.toFixed(2)}
                  </td>
                  <td className={`px-4 py-3 text-sm font-mono font-bold text-right ${
                    getPairCostColor(trade.resulting_pair_cost)
                  }`}>
                    ${trade.resulting_pair_cost.toFixed(4)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
