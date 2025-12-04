// Core Types
export interface Trade {
  id: string;
  timestamp: string;
  side: 'YES' | 'NO';
  price: number;
  quantity: number;
  resulting_pair_cost: number;
  cost: number;
}

export interface Position {
  yes_shares: number;
  no_shares: number;
  total_cost_basis: number;
  locked_pairs: number;
  locked_profit: number;
  delta_exposure: number;
  current_pair_cost: number;
}

export interface MarketInfo {
  market_id: string;
  market_title: string;
  expiration_time: string;
  yes_price: number;
  no_price: number;
  sum_price: number;
}

export interface OrderBookLevel {
  price: number;
  quantity: number;
}

export interface OrderBook {
  yes_bids: OrderBookLevel[];
  yes_asks: OrderBookLevel[];
  no_bids: OrderBookLevel[];
  no_asks: OrderBookLevel[];
}

export interface BotStatus {
  is_active: boolean;
  is_accumulating: boolean;
  position: Position;
  market: MarketInfo;
  last_updated: string;
}

export interface AccumulationPoint {
  timestamp: string;
  yes_shares: number;
  no_shares: number;
}

export interface ExposurePoint {
  timestamp: string;
  total_cost: number;
  guaranteed_payout: number;
  locked_profit: number;
}

export interface ArbitragePoint {
  timestamp: string;
  sum_price: number;
}

export interface WebSocketMessage {
  type: 'trade' | 'position' | 'market' | 'orderbook' | 'status';
  data: any;
}

export interface RiskStatus {
  delta_status: 'safe' | 'warning' | 'danger';
  liquidity_status: 'good' | 'low' | 'critical';
  api_connected: boolean;
  time_buffer_minutes: number;
}
