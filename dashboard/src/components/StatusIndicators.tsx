'use client';

import { RiskStatus } from '@/types';
import { Shield, Droplets, Wifi, Clock, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

interface StatusIndicatorsProps {
  riskStatus: RiskStatus | null;
}

export default function StatusIndicators({ riskStatus }: StatusIndicatorsProps) {
  const getDeltaStatusColor = (status: string) => {
    switch (status) {
      case 'safe':
        return 'text-green-400 bg-green-900/20 border-green-700';
      case 'warning':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
      case 'danger':
        return 'text-red-400 bg-red-900/20 border-red-700';
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-700';
    }
  };

  const getLiquidityStatusColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'text-green-400 bg-green-900/20 border-green-700';
      case 'low':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
      case 'critical':
        return 'text-red-400 bg-red-900/20 border-red-700';
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-700';
    }
  };

  const getDeltaIcon = (status: string) => {
    switch (status) {
      case 'safe':
        return <CheckCircle2 className="w-5 h-5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5" />;
      case 'danger':
        return <XCircle className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  const getLiquidityIcon = (status: string) => {
    switch (status) {
      case 'good':
        return <CheckCircle2 className="w-5 h-5" />;
      case 'low':
        return <AlertTriangle className="w-5 h-5" />;
      case 'critical':
        return <XCircle className="w-5 h-5" />;
      default:
        return <Droplets className="w-5 h-5" />;
    }
  };

  const getTimeBufferColor = (minutes: number) => {
    if (minutes > 60) return 'text-green-400 bg-green-900/20 border-green-700';
    if (minutes > 30) return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
    return 'text-red-400 bg-red-900/20 border-red-700';
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-xl">
      <div className="mb-3">
        <h3 className="text-lg font-bold text-white">Risk Status</h3>
        <p className="text-sm text-gray-400">Real-time monitoring</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Delta Status */}
        <div className={`border rounded-lg p-4 ${getDeltaStatusColor(riskStatus?.delta_status || 'safe')}`}>
          <div className="flex items-center gap-2 mb-2">
            {getDeltaIcon(riskStatus?.delta_status || 'safe')}
            <span className="text-xs font-semibold uppercase">Delta</span>
          </div>
          <div className="text-lg font-bold capitalize">
            {riskStatus?.delta_status || 'Unknown'}
          </div>
          <div className="text-xs mt-1 opacity-80">
            Position balance
          </div>
        </div>

        {/* Liquidity Status */}
        <div className={`border rounded-lg p-4 ${getLiquidityStatusColor(riskStatus?.liquidity_status || 'good')}`}>
          <div className="flex items-center gap-2 mb-2">
            {getLiquidityIcon(riskStatus?.liquidity_status || 'good')}
            <span className="text-xs font-semibold uppercase">Liquidity</span>
          </div>
          <div className="text-lg font-bold capitalize">
            {riskStatus?.liquidity_status || 'Unknown'}
          </div>
          <div className="text-xs mt-1 opacity-80">
            Market depth
          </div>
        </div>

        {/* API Connection */}
        <div className={`border rounded-lg p-4 ${
          riskStatus?.api_connected
            ? 'text-green-400 bg-green-900/20 border-green-700'
            : 'text-red-400 bg-red-900/20 border-red-700'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <Wifi className="w-5 h-5" />
            <span className="text-xs font-semibold uppercase">API</span>
          </div>
          <div className="text-lg font-bold">
            {riskStatus?.api_connected ? 'Connected' : 'Disconnected'}
          </div>
          <div className="text-xs mt-1 opacity-80">
            Exchange link
          </div>
        </div>

        {/* Time Buffer */}
        <div className={`border rounded-lg p-4 ${
          getTimeBufferColor(riskStatus?.time_buffer_minutes || 0)
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5" />
            <span className="text-xs font-semibold uppercase">Buffer</span>
          </div>
          <div className="text-lg font-bold">
            {riskStatus?.time_buffer_minutes || 0}m
          </div>
          <div className="text-xs mt-1 opacity-80">
            To settlement
          </div>
        </div>
      </div>

      {/* Status Legend */}
      <div className="mt-4 pt-4 border-t border-gray-800">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-gray-400">Safe / Good</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500" />
            <span className="text-gray-400">Warning / Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-gray-400">Danger / Critical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gray-500" />
            <span className="text-gray-400">Unknown</span>
          </div>
        </div>
      </div>
    </div>
  );
}
