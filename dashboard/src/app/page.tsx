'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import Scoreboard from '@/components/Scoreboard';
import AccumulationChart from '@/components/AccumulationChart';
import ExposureChart from '@/components/ExposureChart';
import ArbitrageChannel from '@/components/ArbitrageChannel';
import OrderBook from '@/components/OrderBook';
import TradeLedger from '@/components/TradeLedger';
import ControlPanel from '@/components/ControlPanel';
import StatusIndicators from '@/components/StatusIndicators';
import {
  BotStatus,
  Trade,
  OrderBook as OrderBookType,
  AccumulationPoint,
  ExposurePoint,
  ArbitragePoint,
  RiskStatus,
} from '@/types';

export default function Dashboard() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [orderBook, setOrderBook] = useState<OrderBookType | null>(null);
  const [accumulationData, setAccumulationData] = useState<AccumulationPoint[]>([]);
  const [exposureData, setExposureData] = useState<ExposurePoint[]>([]);
  const [arbitrageData, setArbitrageData] = useState<ArbitragePoint[]>([]);
  const [riskStatus, setRiskStatus] = useState<RiskStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const { isConnected, lastMessage } = useWebSocket();

  // Initial data fetch
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [statusData, tradesData, orderBookData] = await Promise.all([
          apiClient.fetchStatus().catch(() => null),
          apiClient.fetchTrades(20).catch(() => []),
          apiClient.fetchOrderBook().catch(() => null),
        ]);

        if (statusData) setStatus(statusData);
        if (tradesData) setTrades(tradesData);
        if (orderBookData) setOrderBook(orderBookData);

        // Fetch historical data
        const [accData, expData, arbData] = await Promise.all([
          apiClient.fetchAccumulationHistory().catch(() => []),
          apiClient.fetchExposureHistory().catch(() => []),
          apiClient.fetchArbitrageHistory().catch(() => []),
        ]);

        if (accData) setAccumulationData(accData);
        if (expData) {
          const exposurePoints = expData.map((point: any) => ({
            timestamp: point.timestamp,
            total_cost: point.total_cost,
            guaranteed_payout: point.guaranteed_payout,
            locked_profit: point.guaranteed_payout - point.total_cost,
          }));
          setExposureData(exposurePoints);
        }
        if (arbData) setArbitrageData(arbData);
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();

    // Refresh data every 5 seconds
    const interval = setInterval(fetchInitialData, 5000);

    return () => clearInterval(interval);
  }, []);

  // Handle WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    const { type, data } = lastMessage;

    switch (type) {
      case 'trade':
        setTrades((prev) => [data, ...prev.slice(0, 19)]);
        // Update accumulation data
        setAccumulationData((prev) => [
          ...prev,
          {
            timestamp: data.timestamp,
            yes_shares: data.side === 'YES' ? data.quantity : 0,
            no_shares: data.side === 'NO' ? data.quantity : 0,
          },
        ]);
        break;

      case 'position':
        setStatus((prev) => (prev ? { ...prev, position: data } : null));
        break;

      case 'market':
        setStatus((prev) => (prev ? { ...prev, market: data } : null));
        // Update arbitrage data
        setArbitrageData((prev) => [
          ...prev,
          {
            timestamp: new Date().toISOString(),
            sum_price: data.yes_price + data.no_price,
          },
        ]);
        break;

      case 'orderbook':
        setOrderBook(data);
        break;

      case 'status':
        setStatus(data);
        break;

      default:
        break;
    }
  }, [lastMessage]);

  // Calculate risk status
  useEffect(() => {
    if (!status) return;

    const deltaExposure = Math.abs(status.position.delta_exposure);
    const totalShares = status.position.yes_shares + status.position.no_shares;
    const deltaPercentage = totalShares > 0 ? deltaExposure / totalShares : 0;

    let delta_status: 'safe' | 'warning' | 'danger' = 'safe';
    if (deltaPercentage > 0.2) delta_status = 'danger';
    else if (deltaPercentage > 0.1) delta_status = 'warning';

    const expiration = new Date(status.market.expiration_time).getTime();
    const now = new Date().getTime();
    const time_buffer_minutes = Math.floor((expiration - now) / (1000 * 60));

    setRiskStatus({
      delta_status,
      liquidity_status: 'good', // TODO: Calculate based on order book
      api_connected: isConnected,
      time_buffer_minutes,
    });
  }, [status, isConnected]);

  // Control handlers
  const handlePanicClose = async () => {
    try {
      const result = await apiClient.panicClose();
      console.log('Panic close result:', result);
      alert(result.message);
    } catch (error) {
      console.error('Failed to panic close:', error);
      alert('Failed to execute panic close');
    }
  };

  const handleHaltAccumulation = async () => {
    try {
      const result = await apiClient.haltAccumulation();
      console.log('Halt result:', result);
    } catch (error) {
      console.error('Failed to halt accumulation:', error);
    }
  };

  const handleResumeAccumulation = async () => {
    try {
      const result = await apiClient.resumeAccumulation();
      console.log('Resume result:', result);
    } catch (error) {
      console.error('Failed to resume accumulation:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Loading Gabagool Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 p-4">
      <div className="max-w-[1920px] mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-white">
            Gabagool <span className="text-blue-400">Volatility Arbitrage</span>
          </h1>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Scoreboard */}
        <Scoreboard market={status?.market || null} position={status?.position || null} />

        {/* Status Indicators */}
        <StatusIndicators riskStatus={riskStatus} />

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[400px]">
          <AccumulationChart data={accumulationData} />
          <ExposureChart data={exposureData} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[400px]">
          <ArbitrageChannel data={arbitrageData} />
          <OrderBook orderBook={orderBook} />
        </div>

        {/* Trade Ledger */}
        <TradeLedger trades={trades} />

        {/* Control Panel */}
        <ControlPanel
          isActive={status?.is_active || false}
          isAccumulating={status?.is_accumulating || false}
          onPanicClose={handlePanicClose}
          onHaltAccumulation={handleHaltAccumulation}
          onResumeAccumulation={handleResumeAccumulation}
        />
      </div>
    </div>
  );
}
