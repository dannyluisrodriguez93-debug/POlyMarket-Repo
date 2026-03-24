"""Demo mode — simulated Kalshi client with realistic market data."""

import random
import uuid
from datetime import datetime, timedelta, timezone


def _generate_demo_markets() -> list[dict]:
    """Generate realistic-looking Kalshi demo markets."""
    now = datetime.now(timezone.utc)

    # Short-term markets (closing within 24 hours)
    short_term = [
        {"title": "Will the S&P 500 close above 5,800 today?", "ticker": "SP500-25MAR24-T5800", "event_ticker": "SP500-25MAR24"},
        {"title": "Will Bitcoin be above $95,000 at midnight?", "ticker": "BTC-25MAR24-T95K", "event_ticker": "BTC-25MAR24"},
        {"title": "Will the Fed Funds Rate stay unchanged this week?", "ticker": "FED-RATE-HOLD-25MAR", "event_ticker": "FED-RATE-25MAR"},
        {"title": "Will US GDP growth exceed 2.5% this quarter?", "ticker": "GDP-Q1-25-T2.5", "event_ticker": "GDP-Q1-25"},
        {"title": "Will the 10-year Treasury yield stay below 4.5%?", "ticker": "TNOTE-25MAR-U4.5", "event_ticker": "TNOTE-25MAR"},
        {"title": "Will natural gas prices rise above $4/MMBtu today?", "ticker": "NATGAS-25MAR-T4", "event_ticker": "NATGAS-25MAR"},
        {"title": "Will the NASDAQ close higher than yesterday?", "ticker": "NASDAQ-UP-25MAR24", "event_ticker": "NASDAQ-25MAR24"},
        {"title": "Will Tesla close above $175 today?", "ticker": "TSLA-25MAR24-T175", "event_ticker": "TSLA-25MAR24"},
        {"title": "Will gold close above $3,050/oz today?", "ticker": "GOLD-25MAR24-T3050", "event_ticker": "GOLD-25MAR24"},
        {"title": "Will crude oil stay above $68/barrel today?", "ticker": "OIL-25MAR24-T68", "event_ticker": "OIL-25MAR24"},
        {"title": "Will the VIX close below 15 today?", "ticker": "VIX-25MAR24-U15", "event_ticker": "VIX-25MAR24"},
        {"title": "Will the US Dollar Index rise today?", "ticker": "DXY-UP-25MAR24", "event_ticker": "DXY-25MAR24"},
    ]

    # Long-term markets (closing in 30-60 days)
    long_term = [
        {"title": "Will the Fed cut rates by June 2026?", "ticker": "FED-CUT-JUN26", "event_ticker": "FED-POLICY-2026"},
        {"title": "Will US unemployment stay below 4.5% through May?", "ticker": "UNEMP-U4.5-MAY26", "event_ticker": "UNEMP-2026"},
        {"title": "Will S&P 500 be above 5,500 on April 30?", "ticker": "SP500-APR30-T5500", "event_ticker": "SP500-APR26"},
        {"title": "Will Bitcoin be above $80,000 on May 1?", "ticker": "BTC-MAY1-T80K", "event_ticker": "BTC-MAY26"},
        {"title": "Will core CPI stay below 3.5% in April report?", "ticker": "CPI-APR26-U3.5", "event_ticker": "CPI-APR26"},
        {"title": "Will the 30-year mortgage rate drop below 6.5%?", "ticker": "MORT30-U6.5-MAY26", "event_ticker": "MORT-2026"},
        {"title": "Will US retail sales grow in Q1 2026?", "ticker": "RETAIL-GROW-Q1-26", "event_ticker": "RETAIL-Q1-26"},
        {"title": "Will Nvidia stock be above $130 on May 1?", "ticker": "NVDA-MAY1-T130", "event_ticker": "NVDA-MAY26"},
    ]

    # Medium-term extras
    medium_term = [
        {"title": "Will there be a government shutdown before April 15?", "ticker": "GOVSHUT-APR15", "event_ticker": "GOVSHUT-2026"},
        {"title": "Will US home prices increase in March?", "ticker": "HOME-PRICE-UP-MAR26", "event_ticker": "HOME-MAR26"},
        {"title": "Will the Euro strengthen against the Dollar this month?", "ticker": "EURUSD-UP-MAR26", "event_ticker": "EURUSD-MAR26"},
        {"title": "Will Apple announce a new product in April?", "ticker": "AAPL-PRODUCT-APR26", "event_ticker": "AAPL-APR26"},
    ]

    markets = []

    # Build short-term markets
    for m in short_term:
        hours_to_close = random.uniform(1.5, 22)
        close_time = (now + timedelta(hours=hours_to_close)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Generate prices that produce interesting opportunities
        # High-probability ones (good for the strategy)
        if random.random() < 0.6:
            yes_price = random.choice([85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95])
        else:
            yes_price = random.randint(40, 80)

        no_price = 100 - yes_price
        volume = random.randint(3000, 150000)

        markets.append({
            "ticker": m["ticker"],
            "title": m["title"],
            "event_ticker": m["event_ticker"],
            "status": "open",
            "yes_price": yes_price,
            "no_price": no_price,
            "close_time": close_time,
            "volume": volume,
        })

    # Build long-term markets
    for m in long_term:
        days_to_close = random.randint(30, 58)
        close_time = (now + timedelta(days=days_to_close)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # High-probability ones for LT strategy
        if random.random() < 0.5:
            yes_price = random.choice([90, 91, 92, 93, 94, 95])
        else:
            yes_price = random.randint(50, 89)

        no_price = 100 - yes_price
        volume = random.randint(10000, 500000)

        markets.append({
            "ticker": m["ticker"],
            "title": m["title"],
            "event_ticker": m["event_ticker"],
            "status": "open",
            "yes_price": yes_price,
            "no_price": no_price,
            "close_time": close_time,
            "volume": volume,
        })

    # Build medium-term markets (won't match either strategy — that's fine)
    for m in medium_term:
        days_to_close = random.randint(5, 25)
        close_time = (now + timedelta(days=days_to_close)).strftime("%Y-%m-%dT%H:%M:%SZ")
        yes_price = random.randint(30, 85)
        no_price = 100 - yes_price
        volume = random.randint(5000, 200000)

        markets.append({
            "ticker": m["ticker"],
            "title": m["title"],
            "event_ticker": m["event_ticker"],
            "status": "open",
            "yes_price": yes_price,
            "no_price": no_price,
            "close_time": close_time,
            "volume": volume,
        })

    return markets


class DemoKalshiClient:
    """Simulated Kalshi client for demo mode."""

    def __init__(self, starting_balance_cents: int = 50000):
        self._balance_cents = starting_balance_cents
        self._markets = _generate_demo_markets()
        self._orders: list[dict] = []

    def login(self) -> bool:
        return True

    def get_balance(self) -> dict:
        return {"available_balance": self._balance_cents}

    def fetch_all_markets(self) -> list[dict]:
        return list(self._markets)

    def get_market(self, ticker: str) -> dict:
        for m in self._markets:
            if m["ticker"] == ticker:
                return m
        return {}

    def place_order(self, **kwargs) -> dict:
        order_id = f"demo-{uuid.uuid4().hex[:12]}"
        count = kwargs.get("count", 1)
        price = kwargs.get("yes_price") or kwargs.get("no_price") or 90
        cost = count * price

        if cost > self._balance_cents:
            raise ValueError(f"Insufficient balance: need ${cost/100:.2f}, have ${self._balance_cents/100:.2f}")

        self._balance_cents -= cost

        order = {
            "order_id": order_id,
            "ticker": kwargs.get("ticker", ""),
            "side": kwargs.get("side", "yes"),
            "action": kwargs.get("action", "buy"),
            "count": count,
            "yes_price": kwargs.get("yes_price"),
            "no_price": kwargs.get("no_price"),
            "type": kwargs.get("order_type", "limit"),
            "status": "resting",
            "remaining_count": count,
        }
        self._orders.append(order)
        return {"order": order}

    def get_orders(self, status: str | None = None) -> list[dict]:
        if status:
            return [o for o in self._orders if o["status"] == status]
        return list(self._orders)

    def cancel_order(self, order_id: str) -> bool:
        for order in self._orders:
            if order["order_id"] == order_id:
                # Refund
                price = order.get("yes_price") or order.get("no_price") or 0
                self._balance_cents += order["remaining_count"] * price
                order["status"] = "cancelled"
                return True
        return False
