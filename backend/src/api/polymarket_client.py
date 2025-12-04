"""
Polymarket CLOB API client with WebSocket support.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any
import websockets
import httpx
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from src.models.position import OrderBook, OrderBookEntry, MarketInfo
from src.config import get_config

logger = logging.getLogger(__name__)


class PolymarketClient:
    """Client for Polymarket CLOB API."""

    def __init__(self):
        """Initialize Polymarket client."""
        self.config = get_config()
        self.base_url = self.config.polymarket_api_url
        self.api_key = self.config.polymarket_api_key
        self.api_secret = self.config.polymarket_api_secret

        # Initialize Web3 account for signing
        self.account = Account.from_key(self.config.private_key)
        self.address = self.account.address

        self.http_client: Optional[httpx.AsyncClient] = None
        self.ws_connection: Optional[websockets.WebSocketClientProtocol] = None
        self.ws_callbacks: Dict[str, Callable] = {}

        logger.info("Polymarket client initialized for address: %s", self.address)

    async def connect(self):
        """Initialize HTTP client."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                headers={
                    "Content-Type": "application/json",
                }
            )
            logger.info("HTTP client connected to %s", self.base_url)

    async def disconnect(self):
        """Close connections."""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("HTTP client disconnected")

        if self.ws_connection:
            await self.ws_connection.close()
            logger.info("WebSocket disconnected")

    # Authentication

    def _sign_message(self, message: str) -> str:
        """Sign a message with private key."""
        encoded_message = encode_defunct(text=message)
        signed_message = self.account.sign_message(encoded_message)
        return signed_message.signature.hex()

    def _generate_hmac_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC signature for API requests."""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_auth_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate authentication headers."""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_hmac_signature(timestamp, method, path, body)

        return {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
        }

    # Market Data

    async def get_markets(
        self,
        active: bool = True,
        closed: bool = False,
        keywords: Optional[List[str]] = None
    ) -> List[MarketInfo]:
        """
        Get markets from Polymarket.

        Args:
            active: Include active markets
            closed: Include closed markets
            keywords: Filter by keywords (e.g., ["BTC", "ETH"])
        """
        try:
            params = {
                "active": str(active).lower(),
                "closed": str(closed).lower(),
            }

            response = await self.http_client.get("/markets", params=params)
            response.raise_for_status()

            markets_data = response.json()
            markets = []

            for market_data in markets_data:
                # Filter by keywords if provided
                if keywords:
                    question = market_data.get("question", "").upper()
                    if not any(keyword.upper() in question for keyword in keywords):
                        continue

                # Parse market info
                try:
                    market = MarketInfo(
                        market_id=market_data["market_id"],
                        condition_id=market_data["condition_id"],
                        token_id_yes=market_data["tokens"]["YES"],
                        token_id_no=market_data["tokens"]["NO"],
                        question=market_data["question"],
                        description=market_data.get("description"),
                        strike_price=Decimal(market_data["strike_price"]) if "strike_price" in market_data else None,
                        expiration=datetime.fromisoformat(market_data["end_date_iso"].replace("Z", "+00:00")),
                        active=market_data.get("active", True),
                        closed=market_data.get("closed", False),
                        min_tick_size=Decimal(market_data.get("min_tick_size", "0.01")),
                        min_size=Decimal(market_data.get("min_size", "1")),
                    )
                    markets.append(market)

                except Exception as e:
                    logger.warning("Failed to parse market %s: %s", market_data.get("market_id"), e)
                    continue

            logger.info("Retrieved %d markets", len(markets))
            return markets

        except Exception as e:
            logger.error("Error fetching markets: %s", e)
            return []

    async def get_15min_markets(self, asset: str = "BTC") -> List[MarketInfo]:
        """
        Get 15-minute expiration markets for BTC or ETH.

        Args:
            asset: "BTC" or "ETH"
        """
        markets = await self.get_markets(active=True, keywords=[asset, "15"])

        # Filter for 15-minute markets expiring soon
        now = datetime.utcnow()
        fifteen_min_markets = []

        for market in markets:
            time_to_expiry = (market.expiration - now).total_seconds() / 60

            # Markets expiring in 5-20 minutes
            if 5 <= time_to_expiry <= 20 and "15" in market.question:
                fifteen_min_markets.append(market)

        logger.info("Found %d 15-minute %s markets", len(fifteen_min_markets), asset)
        return fifteen_min_markets

    async def get_order_book(self, token_id: str) -> List[OrderBookEntry]:
        """
        Get order book for a token.

        Args:
            token_id: Token ID (YES or NO)

        Returns:
            List of order book entries (sorted by price)
        """
        try:
            response = await self.http_client.get(f"/book?token_id={token_id}")
            response.raise_for_status()

            book_data = response.json()
            entries = []

            # Parse bids
            for bid in book_data.get("bids", []):
                entries.append(OrderBookEntry(
                    price=Decimal(bid["price"]),
                    size=Decimal(bid["size"])
                ))

            logger.debug("Retrieved %d order book entries for token %s", len(entries), token_id)
            return entries

        except Exception as e:
            logger.error("Error fetching order book for %s: %s", token_id, e)
            return []

    async def get_market_order_book(self, market: MarketInfo) -> OrderBook:
        """
        Get complete order book for a market (YES and NO sides).

        Args:
            market: Market info

        Returns:
            OrderBook with all sides
        """
        try:
            # Fetch both sides concurrently
            yes_bids_task = self.http_client.get(f"/book?token_id={market.token_id_yes}&side=BUY")
            yes_asks_task = self.http_client.get(f"/book?token_id={market.token_id_yes}&side=SELL")
            no_bids_task = self.http_client.get(f"/book?token_id={market.token_id_no}&side=BUY")
            no_asks_task = self.http_client.get(f"/book?token_id={market.token_id_no}&side=SELL")

            results = await asyncio.gather(
                yes_bids_task,
                yes_asks_task,
                no_bids_task,
                no_asks_task,
                return_exceptions=True
            )

            # Parse responses
            def parse_book(response) -> List[OrderBookEntry]:
                if isinstance(response, Exception):
                    return []
                try:
                    data = response.json()
                    return [
                        OrderBookEntry(price=Decimal(entry["price"]), size=Decimal(entry["size"]))
                        for entry in data.get("orders", [])
                    ]
                except:
                    return []

            yes_bids = parse_book(results[0])
            yes_asks = parse_book(results[1])
            no_bids = parse_book(results[2])
            no_asks = parse_book(results[3])

            # Sort
            yes_bids.sort(key=lambda x: x.price, reverse=True)
            yes_asks.sort(key=lambda x: x.price)
            no_bids.sort(key=lambda x: x.price, reverse=True)
            no_asks.sort(key=lambda x: x.price)

            order_book = OrderBook(
                yes_bids=yes_bids,
                yes_asks=yes_asks,
                no_bids=no_bids,
                no_asks=no_asks,
            )

            logger.debug("Order book retrieved: YES bids=%d asks=%d, NO bids=%d asks=%d",
                        len(yes_bids), len(yes_asks), len(no_bids), len(no_asks))

            return order_book

        except Exception as e:
            logger.error("Error fetching market order book: %s", e)
            return OrderBook()

    # Order Management

    def _create_order_signature(self, order: Dict[str, Any]) -> str:
        """Create signature for order."""
        # Create EIP-712 structured data
        order_hash = Web3.solidity_keccak(
            ['address', 'address', 'uint256', 'uint256', 'uint256', 'uint256'],
            [
                order['maker'],
                order['taker'],
                int(order['makerAmount']),
                int(order['takerAmount']),
                int(order['expiration']),
                int(order['salt'])
            ]
        )

        # Sign the hash
        signed = self.account.signHash(order_hash)
        return signed.signature.hex()

    async def place_limit_order(
        self,
        token_id: str,
        side: str,
        price: Decimal,
        size: Decimal,
        post_only: bool = True
    ) -> Optional[str]:
        """
        Place a limit order.

        Args:
            token_id: Token ID (YES or NO)
            side: "BUY" or "SELL"
            price: Limit price
            size: Order size
            post_only: Only place order if it doesn't immediately match

        Returns:
            Order ID if successful
        """
        try:
            # Construct order
            salt = int(time.time() * 1000000)
            expiration = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())

            order = {
                "maker": self.address,
                "taker": "0x0000000000000000000000000000000000000000",
                "tokenId": token_id,
                "side": side,
                "price": str(price),
                "size": str(size),
                "expiration": expiration,
                "salt": salt,
                "postOnly": post_only,
            }

            # Sign order
            signature = self._create_order_signature(order)
            order["signature"] = signature

            # Send order
            body = json.dumps(order)
            headers = self._get_auth_headers("POST", "/order", body)

            response = await self.http_client.post(
                "/order",
                json=order,
                headers=headers
            )
            response.raise_for_status()

            result = response.json()
            order_id = result.get("orderID")

            logger.info("Order placed: %s %s %s @ %s, order_id=%s",
                       side, size, token_id[:8], price, order_id)

            return order_id

        except Exception as e:
            logger.error("Error placing order: %s", e)
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful
        """
        try:
            headers = self._get_auth_headers("DELETE", f"/order/{order_id}")

            response = await self.http_client.delete(
                f"/order/{order_id}",
                headers=headers
            )
            response.raise_for_status()

            logger.info("Order cancelled: %s", order_id)
            return True

        except Exception as e:
            logger.error("Error cancelling order %s: %s", order_id, e)
            return False

    async def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get all open orders."""
        try:
            headers = self._get_auth_headers("GET", "/orders")

            response = await self.http_client.get(
                "/orders",
                headers=headers
            )
            response.raise_for_status()

            orders = response.json()
            logger.debug("Retrieved %d open orders", len(orders))
            return orders

        except Exception as e:
            logger.error("Error fetching open orders: %s", e)
            return []

    # WebSocket Streaming

    async def stream_order_book(
        self,
        market: MarketInfo,
        callback: Callable[[OrderBook], None]
    ):
        """
        Stream real-time order book updates via WebSocket.

        Args:
            market: Market to stream
            callback: Function to call with order book updates
        """
        ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://") + "/ws"

        try:
            async with websockets.connect(ws_url) as websocket:
                self.ws_connection = websocket

                # Subscribe to market
                subscribe_msg = {
                    "type": "subscribe",
                    "channel": "book",
                    "market": market.market_id,
                }
                await websocket.send(json.dumps(subscribe_msg))

                logger.info("WebSocket connected, streaming order book for %s", market.market_id)

                # Listen for updates
                async for message in websocket:
                    try:
                        data = json.loads(message)

                        if data.get("type") == "book_update":
                            # Parse order book update
                            order_book = self._parse_ws_order_book(data, market)
                            callback(order_book)

                    except Exception as e:
                        logger.error("Error processing WebSocket message: %s", e)
                        continue

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except Exception as e:
            logger.error("WebSocket error: %s", e)
        finally:
            self.ws_connection = None

    def _parse_ws_order_book(self, data: Dict, market: MarketInfo) -> OrderBook:
        """Parse WebSocket order book data."""
        # This is a simplified parser - adjust based on actual Polymarket WS format
        yes_bids = [
            OrderBookEntry(price=Decimal(e["price"]), size=Decimal(e["size"]))
            for e in data.get("yes_bids", [])
        ]
        yes_asks = [
            OrderBookEntry(price=Decimal(e["price"]), size=Decimal(e["size"]))
            for e in data.get("yes_asks", [])
        ]
        no_bids = [
            OrderBookEntry(price=Decimal(e["price"]), size=Decimal(e["size"]))
            for e in data.get("no_bids", [])
        ]
        no_asks = [
            OrderBookEntry(price=Decimal(e["price"]), size=Decimal(e["size"]))
            for e in data.get("no_asks", [])
        ]

        return OrderBook(
            yes_bids=yes_bids,
            yes_asks=yes_asks,
            no_bids=no_bids,
            no_asks=no_asks,
        )
