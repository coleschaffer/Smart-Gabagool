'use client';

import { OrderBook as OrderBookType } from '@/types';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface OrderBookProps {
  orderBook: OrderBookType | null;
}

export default function OrderBook({ orderBook }: OrderBookProps) {
  const formatPrice = (price: number) => price.toFixed(4);
  const formatQuantity = (qty: number) => qty.toFixed(2);

  const getDepthPercentage = (quantity: number, maxQty: number) => {
    return Math.min((quantity / maxQty) * 100, 100);
  };

  const maxYesQty = Math.max(
    ...((orderBook?.yes_bids || []).map(b => b.quantity)),
    ...((orderBook?.yes_asks || []).map(a => a.quantity)),
    1
  );

  const maxNoQty = Math.max(
    ...((orderBook?.no_bids || []).map(b => b.quantity)),
    ...((orderBook?.no_asks || []).map(a => a.quantity)),
    1
  );

  const OrderBookSide = ({
    title,
    bids,
    asks,
    maxQty,
    color
  }: {
    title: string;
    bids: Array<{ price: number; quantity: number }>;
    asks: Array<{ price: number; quantity: number }>;
    maxQty: number;
    color: 'green' | 'red';
  }) => (
    <div className="flex-1">
      <div className="mb-3">
        <h4 className={`text-sm font-bold ${color === 'green' ? 'text-green-400' : 'text-red-400'} flex items-center gap-2`}>
          {color === 'green' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          {title}
        </h4>
      </div>

      {/* Asks (Sell Orders) */}
      <div className="mb-4">
        <div className="text-xs text-gray-500 mb-1 flex justify-between px-2">
          <span>Price</span>
          <span>Quantity</span>
        </div>
        <div className="space-y-1">
          {asks.length === 0 ? (
            <div className="text-xs text-gray-600 text-center py-2">No asks</div>
          ) : (
            asks.slice(0, 5).map((ask, idx) => (
              <div key={idx} className="relative">
                <div
                  className={`absolute right-0 top-0 bottom-0 ${
                    color === 'green' ? 'bg-green-900/20' : 'bg-red-900/20'
                  }`}
                  style={{ width: `${getDepthPercentage(ask.quantity, maxQty)}%` }}
                />
                <div className="relative flex justify-between px-2 py-1 text-xs font-mono">
                  <span className={color === 'green' ? 'text-green-300' : 'text-red-300'}>
                    ${formatPrice(ask.price)}
                  </span>
                  <span className="text-gray-300">{formatQuantity(ask.quantity)}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Spread */}
      <div className={`border-y ${color === 'green' ? 'border-green-900/50' : 'border-red-900/50'} py-2 mb-4`}>
        <div className="text-center">
          <div className="text-xs text-gray-500">SPREAD</div>
          {bids.length > 0 && asks.length > 0 && (
            <div className="text-xs font-mono text-gray-400">
              ${(asks[0].price - bids[0].price).toFixed(4)}
            </div>
          )}
        </div>
      </div>

      {/* Bids (Buy Orders) */}
      <div>
        <div className="space-y-1">
          {bids.length === 0 ? (
            <div className="text-xs text-gray-600 text-center py-2">No bids</div>
          ) : (
            bids.slice(0, 5).map((bid, idx) => (
              <div key={idx} className="relative">
                <div
                  className={`absolute right-0 top-0 bottom-0 ${
                    color === 'green' ? 'bg-green-900/20' : 'bg-red-900/20'
                  }`}
                  style={{ width: `${getDepthPercentage(bid.quantity, maxQty)}%` }}
                />
                <div className="relative flex justify-between px-2 py-1 text-xs font-mono">
                  <span className={color === 'green' ? 'text-green-400' : 'text-red-400'}>
                    ${formatPrice(bid.price)}
                  </span>
                  <span className="text-gray-300">{formatQuantity(bid.quantity)}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 shadow-xl h-full">
      <div className="mb-3">
        <h3 className="text-lg font-bold text-white">Order Book</h3>
        <p className="text-sm text-gray-400">Live market depth</p>
      </div>

      {!orderBook ? (
        <div className="text-center text-gray-500 py-8">Loading order book...</div>
      ) : (
        <div className="flex gap-4">
          <OrderBookSide
            title="YES Market"
            bids={orderBook.yes_bids}
            asks={orderBook.yes_asks}
            maxQty={maxYesQty}
            color="green"
          />
          <div className="w-px bg-gray-800" />
          <OrderBookSide
            title="NO Market"
            bids={orderBook.no_bids}
            asks={orderBook.no_asks}
            maxQty={maxNoQty}
            color="red"
          />
        </div>
      )}
    </div>
  );
}
