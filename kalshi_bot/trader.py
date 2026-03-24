"""Trade execution for the Kalshi Trading Bot."""

import logging
from dataclasses import dataclass

from .client import KalshiClient
from .market_analyzer import Opportunity

logger = logging.getLogger("kalshi_bot")


@dataclass
class TradeResult:
    success: bool
    order_id: str = ""
    status: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "order_id": self.order_id,
            "status": self.status,
            "error": self.error,
        }


def place_limit_order(
    client: KalshiClient,
    opportunity: Opportunity,
    count: int,
    price_cents: int,
) -> TradeResult:
    """Place a limit order for an opportunity."""
    try:
        kwargs = {
            "ticker": opportunity.ticker,
            "side": opportunity.outcome,
            "action": "buy",
            "count": count,
            "order_type": "limit",
        }
        if opportunity.outcome == "yes":
            kwargs["yes_price"] = price_cents
        else:
            kwargs["no_price"] = price_cents

        result = client.place_order(**kwargs)
        order = result.get("order", result)
        return TradeResult(
            success=True,
            order_id=order.get("order_id", ""),
            status=order.get("status", "submitted"),
        )
    except Exception as e:
        logger.error("Limit order failed: %s", e)
        return TradeResult(success=False, error=str(e))


def place_market_order(
    client: KalshiClient,
    opportunity: Opportunity,
    count: int,
) -> TradeResult:
    """Place a market-like order (limit at 99c to ensure fill)."""
    try:
        kwargs = {
            "ticker": opportunity.ticker,
            "side": opportunity.outcome,
            "action": "buy",
            "count": count,
            "order_type": "limit",
        }
        # Use extreme price to simulate market order
        if opportunity.outcome == "yes":
            kwargs["yes_price"] = 99
        else:
            kwargs["no_price"] = 99

        result = client.place_order(**kwargs)
        order = result.get("order", result)
        return TradeResult(
            success=True,
            order_id=order.get("order_id", ""),
            status=order.get("status", "submitted"),
        )
    except Exception as e:
        logger.error("Market order failed: %s", e)
        return TradeResult(success=False, error=str(e))


def get_open_orders(client: KalshiClient) -> list[dict]:
    """Fetch all open orders."""
    try:
        return client.get_orders(status="resting")
    except Exception as e:
        logger.error("Failed to fetch orders: %s", e)
        return []


def cancel_order(client: KalshiClient, order_id: str) -> bool:
    """Cancel a specific order."""
    try:
        return client.cancel_order(order_id)
    except Exception as e:
        logger.error("Failed to cancel order %s: %s", order_id, e)
        return False


def cancel_all_orders(client: KalshiClient) -> int:
    """Cancel all open orders. Returns number cancelled."""
    orders = get_open_orders(client)
    cancelled = 0
    for order in orders:
        order_id = order.get("order_id", "")
        if order_id and cancel_order(client, order_id):
            cancelled += 1
    return cancelled
