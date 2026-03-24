"""Trade execution — places orders via the CLOB API with approval workflow."""

import logging
from dataclasses import dataclass

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, MarketOrderArgs

from .config import Config
from .market_analyzer import Opportunity

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
    success: bool
    order_id: str | None = None
    message: str = ""


def place_limit_order(
    client: ClobClient,
    opportunity: Opportunity,
    size: float,
    price: float,
) -> TradeResult:
    """Place a limit order for the given opportunity."""
    try:
        tick_size = client.get_tick_size(opportunity.token_id)
        neg_risk = client.get_neg_risk(opportunity.token_id)

        order_args = OrderArgs(
            price=price,
            size=size,
            side=opportunity.suggested_side,
            token_id=opportunity.token_id,
        )

        signed_order = client.create_order(order_args)
        response = client.post_order(signed_order, OrderType.GTC)

        order_id = response.get("orderID", response.get("id", "unknown"))
        logger.info("Limit order placed: %s", order_id)

        return TradeResult(
            success=True,
            order_id=str(order_id),
            message=f"Limit order placed: {opportunity.suggested_side} {size} @ {price}",
        )
    except Exception as e:
        logger.error("Failed to place limit order: %s", e)
        return TradeResult(success=False, message=f"Order failed: {e}")


def place_market_order(
    client: ClobClient,
    opportunity: Opportunity,
    amount: float,
) -> TradeResult:
    """Place a market order (fills at best available price)."""
    try:
        order_args = MarketOrderArgs(
            token_id=opportunity.token_id,
            amount=amount,
        )

        signed_order = client.create_market_order(order_args)
        response = client.post_order(signed_order, OrderType.FOK)

        order_id = response.get("orderID", response.get("id", "unknown"))
        logger.info("Market order placed: %s", order_id)

        return TradeResult(
            success=True,
            order_id=str(order_id),
            message=f"Market order placed: {opportunity.suggested_side} ${amount:.2f}",
        )
    except Exception as e:
        logger.error("Failed to place market order: %s", e)
        return TradeResult(success=False, message=f"Order failed: {e}")


def get_open_orders(client: ClobClient) -> list[dict]:
    """Fetch all open orders."""
    try:
        response = client.get_orders()
        if isinstance(response, dict):
            return response.get("data", [])
        return response if isinstance(response, list) else []
    except Exception as e:
        logger.error("Failed to fetch open orders: %s", e)
        return []


def cancel_order(client: ClobClient, order_id: str) -> bool:
    """Cancel a specific order."""
    try:
        client.cancel(order_id)
        logger.info("Order cancelled: %s", order_id)
        return True
    except Exception as e:
        logger.error("Failed to cancel order %s: %s", order_id, e)
        return False


def cancel_all_orders(client: ClobClient) -> bool:
    """Cancel all open orders."""
    try:
        client.cancel_all()
        logger.info("All orders cancelled.")
        return True
    except Exception as e:
        logger.error("Failed to cancel all orders: %s", e)
        return False
