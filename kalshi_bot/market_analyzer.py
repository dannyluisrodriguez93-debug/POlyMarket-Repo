"""Market analysis for Kalshi - 80%+ high-probability scanner."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("kalshi_bot")


@dataclass
class Opportunity:
    """A high-probability trading opportunity."""

    market_title: str
    ticker: str
    event_ticker: str
    outcome: str  # "yes" or "no"
    probability: float  # 0.0-1.0
    price_cents: int  # What you pay per contract (1-99)
    expected_return: float  # Percentage return if correct
    close_time: str
    volume: int = 0
    strategy: str = "high_probability"
    confidence: str = "HIGH"
    reasoning: str = ""


def find_high_probability_markets(
    markets: list[dict],
    min_probability: float = 0.80,
) -> list[Opportunity]:
    """Scan all markets for outcomes with >= min_probability chance of hitting.

    For each open market:
    - If yes_price >= threshold, it's a high-probability YES opportunity
    - If no_price >= threshold (yes_price <= 1-threshold), it's a high-probability NO opportunity

    Returns opportunities sorted by expected return (highest first).
    """
    opportunities = []

    threshold_cents = int(min_probability * 100)

    for market in markets:
        status = market.get("status", "").lower()
        if status not in ("open", "active"):
            continue

        ticker = market.get("ticker", "")
        title = market.get("title", "")
        event_ticker = market.get("event_ticker", "")
        close_time = market.get("close_time", market.get("expiration_time", ""))
        volume = market.get("volume", 0)

        yes_price = market.get("yes_price")
        no_price = market.get("no_price")

        # Kalshi prices are in cents (1-99)
        # Some API responses may use decimals (0.01-0.99) — normalize
        if yes_price is not None and isinstance(yes_price, float) and yes_price < 1:
            yes_price = int(yes_price * 100)
        if no_price is not None and isinstance(no_price, float) and no_price < 1:
            no_price = int(no_price * 100)

        # Derive missing price from the other (yes + no = 100)
        if yes_price is not None and no_price is None:
            no_price = 100 - yes_price
        elif no_price is not None and yes_price is None:
            yes_price = 100 - no_price

        if yes_price is None or no_price is None:
            continue

        # Check YES side
        if yes_price >= threshold_cents and yes_price < 100:
            expected_return = (100 - yes_price) / yes_price * 100
            opp = Opportunity(
                market_title=title,
                ticker=ticker,
                event_ticker=event_ticker,
                outcome="yes",
                probability=yes_price / 100,
                price_cents=yes_price,
                expected_return=round(expected_return, 2),
                close_time=close_time,
                volume=volume,
                reasoning=f"YES at {yes_price}c — {expected_return:.1f}% return if correct",
            )
            opportunities.append(opp)

        # Check NO side
        if no_price >= threshold_cents and no_price < 100:
            expected_return = (100 - no_price) / no_price * 100
            opp = Opportunity(
                market_title=title,
                ticker=ticker,
                event_ticker=event_ticker,
                outcome="no",
                probability=no_price / 100,
                price_cents=no_price,
                expected_return=round(expected_return, 2),
                close_time=close_time,
                volume=volume,
                reasoning=f"NO at {no_price}c — {expected_return:.1f}% return if correct",
            )
            opportunities.append(opp)

    # Sort by expected return descending (highest payoff near-certainties first)
    opportunities.sort(key=lambda o: o.expected_return, reverse=True)

    logger.info(
        "Found %d opportunities at >= %d%% probability",
        len(opportunities),
        int(min_probability * 100),
    )
    return opportunities


def search_markets(markets: list[dict], query: str) -> list[dict]:
    """Filter markets by keyword search on title."""
    query_lower = query.lower()
    return [m for m in markets if query_lower in m.get("title", "").lower()]


def analyze_all(
    markets: list[dict],
    min_probability: float = 0.80,
) -> dict[str, list[Opportunity]]:
    """Run analysis and return categorized results."""
    high_prob = find_high_probability_markets(markets, min_probability)
    return {"high_probability": high_prob}
