import { BotStatus, Trade, OrderBook, MarketInfo } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Get current bot status and position
  async fetchStatus(): Promise<BotStatus> {
    return this.fetch<BotStatus>('/api/status');
  }

  // Get last N trades
  async fetchTrades(limit: number = 20): Promise<Trade[]> {
    return this.fetch<Trade[]>(`/api/trades?limit=${limit}`);
  }

  // Get current order book
  async fetchOrderBook(): Promise<OrderBook> {
    return this.fetch<OrderBook>('/api/orderbook');
  }

  // Get current market information
  async fetchMarketInfo(): Promise<MarketInfo> {
    return this.fetch<MarketInfo>('/api/market');
  }

  // Emergency close all positions
  async panicClose(): Promise<{ success: boolean; message: string }> {
    return this.fetch('/api/panic', {
      method: 'POST',
    });
  }

  // Stop accumulation (halt buying)
  async haltAccumulation(): Promise<{ success: boolean; message: string }> {
    return this.fetch('/api/halt', {
      method: 'POST',
    });
  }

  // Resume accumulation
  async resumeAccumulation(): Promise<{ success: boolean; message: string }> {
    return this.fetch('/api/resume', {
      method: 'POST',
    });
  }

  // Get historical accumulation data
  async fetchAccumulationHistory(): Promise<Array<{ timestamp: string; yes_shares: number; no_shares: number }>> {
    return this.fetch('/api/history/accumulation');
  }

  // Get historical exposure data
  async fetchExposureHistory(): Promise<Array<{ timestamp: string; total_cost: number; guaranteed_payout: number }>> {
    return this.fetch('/api/history/exposure');
  }

  // Get historical arbitrage channel data
  async fetchArbitrageHistory(): Promise<Array<{ timestamp: string; sum_price: number }>> {
    return this.fetch('/api/history/arbitrage');
  }
}

export const apiClient = new ApiClient();

// WebSocket connection helper
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Set<(data: any) => void> = new Set();

  constructor(url: string = API_BASE_URL.replace('http', 'ws')) {
    this.url = `${url}/ws`;
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.messageHandlers.forEach(handler => handler(data));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected, attempting to reconnect...');
        this.reconnect();
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.reconnect();
    }
  }

  private reconnect() {
    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      console.log('Reconnecting WebSocket...');
      this.connect();
    }, this.reconnectInterval);
  }

  subscribe(handler: (data: any) => void) {
    this.messageHandlers.add(handler);
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageHandlers.clear();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
