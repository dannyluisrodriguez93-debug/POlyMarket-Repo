"""Market analysis — fetches markets, detects opportunities, and ranks them."""

import logging
from dataclasses import dataclass
from py_clob_client.client import ClobClient

from .client import fetch_all_markets

logger = logging.getLogger(__name__)


@dataclass
class Opportunity:
    """A detected trading opportunity."""

    market_question: str
    condition_id: str
    token_id: str
    outcome: str
    current_price: float
    midpoint: float
    spread: float
    strategy: str
    reasoning: str
    suggested_side: str  # "BUY" or "SELL"
    confidence: str  # "LOW", "MEDIUM", "HIGH"

    @property
    def implied_probability(self) -> float:
        return self.current_price

    @property
    def potential_return(self) -> float:
        if self.suggested_side == "BUY" and self.current_price > 0:
            return (1.0 / self.current_price - 1.0) * 100
        return 0.0


def search_markets(markets: list[dict], query: str) -> list[dict]:
    """Filter markets by search query (case-insensitive match on question)."""
    query_lower = query.lower()
    return [m for m in markets if query_lower in m.get("question", "").lower()]


def get_market_details(client: ClobClient, market: dict) -> dict:
    """Enrich a market with order book data."""
    tokens = market.get("tokens", [])
    details = {**market, "token_details": []}

    for token in tokens:
        token_id = token.get("token_id", "")
        if not token_id:
            continue
        try:
            orderbook = client.get_order_book(token_id)
            midpoint = client.get_midpoint(token_id)
            spread = client.get_spread(token_id)
            details["token_details"].append(
                {
                    "token_id": token_id,
                    "outcome": token.get("outcome", "Unknown"),
                    "orderbook": orderbook,
                    "midpoint": float(midpoint) if midpoint else None,
                    "spread": float(spread) if spread else None,
                }
            )
        except Exception as e:
            logger.warning("Failed to get details for token %s: %s", token_id, e)

    return details


def find_undervalued_outcomes(
    client: ClobClient, markets: list[dict], max_price: float = 0.30
) -> list[Opportunity]:
    """Find outcomes priced low that might be undervalued (long-shot strategy)."""
    opportunities = []

    for market in markets:
        tokens = market.get("tokens", [])
        for token in tokens:
            token_id = token.get("token_id", "")
            price_str = token.get("price")
            if not token_id or not price_str:
                continue

            try:
                price = float(price_str)
            except (ValueError, TypeError):
                continue

            if 0.01 < price <= max_price:
                try:
                    spread_val = client.get_spread(token_id)
                    spread = float(spread_val) if spread_val else 1.0
                except Exception:
                    spread = 1.0

                potential_return = (1.0 / price - 1.0) * 100
                opportunities.append(
                    Opportunity(
                        market_question=market.get("question", "Unknown"),
                        condition_id=market.get("condition_id", ""),
                        token_id=token_id,
                        outcome=token.get("outcome", "Unknown"),
                        current_price=price,
                        midpoint=price,
                        spread=spread,
                        strategy="undervalued_longshot",
                        reasoning=(
                            f"Outcome priced at {price:.2f} "
                            f"({potential_return:.0f}% potential return if wins). "
                            f"Spread: {spread:.4f}"
                        ),
                        suggested_side="BUY",
                        confidence="LOW",
                    )
                )

    opportunities.sort(key=lambda o: o.current_price)
    return opportunities


def find_wide_spread_opportunities(
    client: ClobClient, markets: list[dict], min_spread: float = 0.03
) -> list[Opportunity]:
    """Find markets with wide bid-ask spreads (market-making opportunity)."""
    opportunities = []

    for market in markets:
        tokens = market.get("tokens", [])
        for token in tokens:
            token_id = token.get("token_id", "")
            if not token_id:
                continue

            try:
                spread_val = client.get_spread(token_id)
                midpoint_val = client.get_midpoint(token_id)
                spread = float(spread_val) if spread_val else 0
                midpoint = float(midpoint_val) if midpoint_val else 0
            except Exception:
                continue

            if spread >= min_spread and midpoint > 0:
                opportunities.append(
                    Opportunity(
                        market_question=market.get("question", "Unknown"),
                        condition_id=market.get("condition_id", ""),
                        token_id=token_id,
                        outcome=token.get("outcome", "Unknown"),
                        current_price=midpoint,
                        midpoint=midpoint,
                        spread=spread,
                        strategy="wide_spread",
                        reasoning=(
                            f"Wide spread of {spread:.4f} around midpoint {midpoint:.4f}. "
                            f"Market-making opportunity: buy at bid, sell at ask."
                        ),
                        suggested_side="BUY",
                        confidence="MEDIUM",
                    )
                )

    opportunities.sort(key=lambda o: o.spread, reverse=True)
    return opportunities


def find_mispriced_pairs(markets: list[dict]) -> list[Opportunity]:
    """Find binary markets where Yes + No prices don't sum to ~1.0 (arbitrage)."""
    opportunities = []

    for market in markets:
        tokens = market.get("tokens", [])
        if len(tokens) != 2:
            continue

        try:
            prices = [float(t.get("price", 0)) for t in tokens]
        except (ValueError, TypeError):
            continue

        price_sum = sum(prices)
        if price_sum == 0:
            continue

        deviation = abs(price_sum - 1.0)
        if deviation > 0.02:
            # Prices don't add up — potential arbitrage
            if price_sum < 0.98:
                # Both outcomes are underpriced, buy both
                reasoning = (
                    f"Prices sum to {price_sum:.4f} (< 1.0). "
                    f"Buy both outcomes for guaranteed profit of {1.0 - price_sum:.4f} per share."
                )
                confidence = "HIGH" if deviation > 0.05 else "MEDIUM"
            else:
                # Both outcomes are overpriced
                reasoning = (
                    f"Prices sum to {price_sum:.4f} (> 1.0). "
                    f"Outcomes may be overpriced."
                )
                confidence = "LOW"

            opportunities.append(
                Opportunity(
                    market_question=market.get("question", "Unknown"),
                    condition_id=market.get("condition_id", ""),
                    token_id=tokens[0].get("token_id", ""),
                    outcome="ARBITRAGE",
                    current_price=prices[0],
                    midpoint=prices[0],
                    spread=deviation,
                    strategy="mispriced_pair",
                    reasoning=reasoning,
                    suggested_side="BUY",
                    confidence=confidence,
                )
            )

    opportunities.sort(key=lambda o: o.spread, reverse=True)
    return opportunities


def analyze_all(
    client: ClobClient, markets: list[dict]
) -> dict[str, list[Opportunity]]:
    """Run all analysis strategies and return categorized opportunities."""
    logger.info("Running analysis on %d markets...", len(markets))

    results = {
        "arbitrage": find_mispriced_pairs(markets),
        "undervalued": find_undervalued_outcomes(client, markets),
        "wide_spread": find_wide_spread_opportunities(client, markets),
    }

    total = sum(len(v) for v in results.values())
    logger.info("Found %d total opportunities.", total)
    return results
