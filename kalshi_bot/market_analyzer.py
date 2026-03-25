"""Market analysis for Kalshi — dual-strategy scanner (short-term + long-term)."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from .config import Config

logger = logging.getLogger("kalshi_bot")


@dataclass
class Opportunity:
    """A trading opportunity."""

    market_title: str
    ticker: str
    event_ticker: str
    outcome: str  # "yes" or "no"
    probability: float  # 0.0-1.0
    price_cents: int  # What you pay per contract (1-99)
    expected_return: float  # Percentage return if correct
    close_time: str
    volume: int = 0
    strategy: str = "short_term"  # "short_term" or "long_term"
    confidence: str = "HIGH"
    reasoning: str = ""
    hours_to_close: float = 0.0
    spread_pct: float = 0.0


def _parse_close_time(close_time: str) -> datetime | None:
    """Parse close_time string to datetime."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(close_time, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _hours_until(close_time: str) -> float | None:
    """Calculate hours until close time."""
    dt = _parse_close_time(close_time)
    if dt is None:
        return None
    delta = dt - datetime.now(timezone.utc)
    return max(0.0, delta.total_seconds() / 3600)


def _normalize_price(price) -> int | None:
    """Normalize price to cents (integer 1-99)."""
    if price is None:
        return None
    if isinstance(price, float) and price < 1:
        return int(price * 100)
    return int(price)


def _extract_market_data(market: dict) -> dict | None:
    """Extract and normalize common market fields."""
    status = market.get("status", "").lower()
    if status not in ("open", "active"):
        return None

    yes_price = _normalize_price(market.get("yes_price"))
    no_price = _normalize_price(market.get("no_price"))

    if yes_price is not None and no_price is None:
        no_price = 100 - yes_price
    elif no_price is not None and yes_price is None:
        yes_price = 100 - no_price

    if yes_price is None or no_price is None:
        return None

    close_time = market.get("close_time", market.get("expiration_time", ""))
    hours = _hours_until(close_time) if close_time else None

    spread = abs(yes_price + no_price - 100) / 100.0

    return {
        "ticker": market.get("ticker", ""),
        "title": market.get("title", ""),
        "event_ticker": market.get("event_ticker", ""),
        "close_time": close_time,
        "volume": market.get("volume", 0),
        "yes_price": yes_price,
        "no_price": no_price,
        "hours_to_close": hours,
        "spread_pct": spread,
    }


def find_short_term_opportunities(
    markets: list[dict],
    config: Config,
) -> list[Opportunity]:
    """Scan for short-term scalping opportunities (0-24h resolution).

    Criteria:
    - Resolution: 0-24h (ideal <12h)
    - Probability: >=85% (primary), 80-84% with momentum
    - Volume: >=$5,000 or spread <=2-3%
    - Price: 80-95 cents (avoid >96)
    """
    opportunities = []

    for market in markets:
        data = _extract_market_data(market)
        if data is None:
            continue

        hours = data["hours_to_close"]
        if hours is None or hours > config.st_max_hours_to_close:
            continue

        volume = data["volume"]
        spread = data["spread_pct"]

        # Liquidity check: volume >= $5,000 OR spread <= 3%
        if volume < config.st_min_volume and spread > config.st_max_spread:
            continue

        for side, price in [("yes", data["yes_price"]), ("no", data["no_price"])]:
            prob = price / 100.0

            # Price range: 80-95 cents
            if price < int(config.st_momentum_probability * 100) or price > config.st_max_price:
                continue

            # Probability gating
            if prob >= config.st_min_probability:
                confidence = "HIGH"
            elif prob >= config.st_momentum_probability:
                # 80-84% only allowed — flagged as momentum-dependent
                confidence = "MOMENTUM"
            else:
                continue

            expected_return = (100 - price) / price * 100

            # Prioritize ideal timeframe
            time_label = "ideal" if hours <= config.st_ideal_hours_to_close else "acceptable"

            opp = Opportunity(
                market_title=data["title"],
                ticker=data["ticker"],
                event_ticker=data["event_ticker"],
                outcome=side,
                probability=prob,
                price_cents=price,
                expected_return=round(expected_return, 2),
                close_time=data["close_time"],
                volume=volume,
                strategy="short_term",
                confidence=confidence,
                hours_to_close=round(hours, 1),
                spread_pct=round(spread, 4),
                reasoning=(
                    f"{side.upper()} @ {price}c | {expected_return:.1f}% return | "
                    f"{hours:.1f}h to close ({time_label}) | "
                    f"vol ${volume:,} | conf {confidence}"
                ),
            )
            opportunities.append(opp)

    # Sort: HIGH confidence first, then by hours_to_close (soonest first), then expected return
    opportunities.sort(
        key=lambda o: (
            0 if o.confidence == "HIGH" else 1,
            o.hours_to_close,
            -o.expected_return,
        )
    )

    logger.info("Short-term scan: %d opportunities", len(opportunities))
    return opportunities


def find_long_term_opportunities(
    markets: list[dict],
    config: Config,
) -> list[Opportunity]:
    """Scan for long-term high-certainty holds (30-60 day horizon).

    Criteria:
    - Probability: >=90-95% ONLY
    - Time horizon: 30-60 days
    - Pricing: 85-95 cents
    - Structural inevitability or strong statistical asymmetry
    """
    opportunities = []

    for market in markets:
        data = _extract_market_data(market)
        if data is None:
            continue

        hours = data["hours_to_close"]
        if hours is None:
            continue

        days = hours / 24.0
        if days < config.lt_min_days_to_close or days > config.lt_max_days_to_close:
            continue

        spread = data["spread_pct"]
        if spread > config.lt_max_spread:
            continue

        for side, price in [("yes", data["yes_price"]), ("no", data["no_price"])]:
            prob = price / 100.0

            # Strict: 90%+ only
            if prob < config.lt_min_probability:
                continue

            # Price range: 85-95 cents
            if price < config.lt_min_price or price > config.lt_max_price:
                continue

            expected_return = (100 - price) / price * 100

            opp = Opportunity(
                market_title=data["title"],
                ticker=data["ticker"],
                event_ticker=data["event_ticker"],
                outcome=side,
                probability=prob,
                price_cents=price,
                expected_return=round(expected_return, 2),
                close_time=data["close_time"],
                volume=data["volume"],
                strategy="long_term",
                confidence="HIGH",
                hours_to_close=round(hours, 1),
                spread_pct=round(spread, 4),
                reasoning=(
                    f"{side.upper()} @ {price}c | {expected_return:.1f}% return | "
                    f"{days:.0f} days to close | hold-to-resolution"
                ),
            )
            opportunities.append(opp)

    # Sort by probability descending (highest certainty first)
    opportunities.sort(key=lambda o: (-o.probability, -o.expected_return))

    logger.info("Long-term scan: %d opportunities", len(opportunities))
    return opportunities


def search_markets(markets: list[dict], query: str) -> list[dict]:
    """Filter markets by keyword search on title."""
    query_lower = query.lower()
    return [m for m in markets if query_lower in m.get("title", "").lower()]


def analyze_all(
    markets: list[dict],
    config: Config,
) -> dict[str, list[Opportunity]]:
    """Run both short-term and long-term analysis."""
    return {
        "short_term": find_short_term_opportunities(markets, config),
        "long_term": find_long_term_opportunities(markets, config),
    }
