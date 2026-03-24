"""Strategy engine — position sizing, risk management, hot state, and kill switch."""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .config import Config
from .market_analyzer import Opportunity

logger = logging.getLogger("kalshi_bot")


@dataclass
class Position:
    """An active position."""

    ticker: str
    side: str
    entry_price: int  # cents
    count: int
    cost_cents: int  # total cost
    strategy: str  # "short_term" or "long_term"
    entry_time: float = 0.0  # timestamp
    last_price: int = 0  # current price for P&L tracking

    @property
    def unrealized_pnl_cents(self) -> int:
        return (self.last_price - self.entry_price) * self.count

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_cents == 0:
            return 0.0
        return self.unrealized_pnl_cents / self.cost_cents


@dataclass
class StrategyState:
    """Tracks the bot's live trading state."""

    # Equity tracking
    starting_balance_cents: int = 0
    peak_equity_cents: int = 0
    current_balance_cents: int = 0

    # Positions
    positions: list[Position] = field(default_factory=list)

    # Daily trade counter
    trades_today: int = 0
    trade_day: str = ""  # YYYY-MM-DD

    # Hot state
    hot_state_active: bool = False

    # Kill switch
    killed: bool = False

    # Session P&L
    session_pnl_cents: int = 0

    @property
    def short_term_positions(self) -> list[Position]:
        return [p for p in self.positions if p.strategy == "short_term"]

    @property
    def long_term_positions(self) -> list[Position]:
        return [p for p in self.positions if p.strategy == "long_term"]

    @property
    def total_deployed_cents(self) -> int:
        return sum(p.cost_cents for p in self.positions)

    @property
    def st_deployed_cents(self) -> int:
        return sum(p.cost_cents for p in self.short_term_positions)

    @property
    def lt_deployed_cents(self) -> int:
        return sum(p.cost_cents for p in self.long_term_positions)

    @property
    def equity_cents(self) -> int:
        unrealized = sum(p.unrealized_pnl_cents for p in self.positions)
        return self.current_balance_cents + self.total_deployed_cents + unrealized

    @property
    def session_pnl_pct(self) -> float:
        if self.starting_balance_cents == 0:
            return 0.0
        return self.session_pnl_cents / self.starting_balance_cents

    @property
    def drawdown_from_peak_pct(self) -> float:
        if self.peak_equity_cents == 0:
            return 0.0
        return (self.peak_equity_cents - self.equity_cents) / self.peak_equity_cents


def initialize_state(balance_cents: int) -> StrategyState:
    """Create initial strategy state from current balance."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return StrategyState(
        starting_balance_cents=balance_cents,
        peak_equity_cents=balance_cents,
        current_balance_cents=balance_cents,
        trade_day=today,
    )


def update_equity(state: StrategyState, balance_cents: int) -> None:
    """Update balance and track peak equity."""
    state.current_balance_cents = balance_cents
    equity = state.equity_cents
    if equity > state.peak_equity_cents:
        state.peak_equity_cents = equity
    state.session_pnl_cents = equity - state.starting_balance_cents


def check_kill_switch(state: StrategyState, config: Config) -> bool:
    """Check if drawdown from peak triggers the kill switch.

    Returns True if trading should be paused.
    """
    if state.killed:
        return True

    drawdown = state.drawdown_from_peak_pct
    if drawdown >= config.kill_switch_drawdown_pct:
        state.killed = True
        logger.warning(
            "KILL SWITCH: Drawdown %.2f%% from peak (threshold %.2f%%)",
            drawdown * 100,
            config.kill_switch_drawdown_pct * 100,
        )
        return True
    return False


def check_hot_state(state: StrategyState, config: Config) -> bool:
    """Check if session P&L triggers hot state (adaptive mode).

    Triggered at +10% to +25% PnL from session start.
    """
    pnl_pct = state.session_pnl_pct
    was_hot = state.hot_state_active

    if config.hot_state_trigger_pct <= pnl_pct <= config.hot_state_max_trigger_pct:
        state.hot_state_active = True
        if not was_hot:
            logger.info("HOT STATE ACTIVATED: Session P&L +%.2f%%", pnl_pct * 100)
    elif pnl_pct > config.hot_state_max_trigger_pct:
        # Above max trigger — stay hot but tighter
        state.hot_state_active = True
    else:
        if was_hot:
            logger.info("HOT STATE DEACTIVATED: Session P&L +%.2f%%", pnl_pct * 100)
        state.hot_state_active = False

    return state.hot_state_active


def calculate_position_size(
    state: StrategyState,
    config: Config,
    opportunity: Opportunity,
) -> int:
    """Calculate how many contracts to buy based on strategy rules.

    Returns count of contracts (0 = do not trade).
    """
    if state.killed:
        return 0

    is_hot = state.hot_state_active
    strategy = opportunity.strategy

    if strategy == "short_term":
        # Check concurrent position limit
        if len(state.short_term_positions) >= config.st_max_concurrent:
            logger.info("Max concurrent ST positions reached (%d)", config.st_max_concurrent)
            return 0

        # Capital available for short-term
        total_st_budget = int(state.current_balance_cents * config.short_term_allocation)

        # Max capital deployed check
        max_deployed = int(state.current_balance_cents * config.st_max_capital_deployed)
        if state.st_deployed_cents >= max_deployed:
            logger.info("Max ST capital deployed (%.0f%%)", config.st_max_capital_deployed * 100)
            return 0

        # Position size
        if is_hot:
            # Hot state: 50-70% of available, but only for 88%+ probability
            if opportunity.probability < config.hot_state_min_probability:
                logger.info("Hot state: skipping %.0f%% prob (need %.0f%%+)",
                            opportunity.probability * 100, config.hot_state_min_probability * 100)
                return 0
            size_budget = int(total_st_budget * config.hot_state_position_size_pct)
        else:
            # Normal: 20-30% per trade
            size_budget = int(total_st_budget * config.st_position_size_pct)

        # Don't exceed remaining deployment room
        remaining = max_deployed - state.st_deployed_cents
        size_budget = min(size_budget, remaining)

        count = size_budget // max(opportunity.price_cents, 1)
        return max(0, count)

    elif strategy == "long_term":
        # Max positions check
        if len(state.long_term_positions) >= config.lt_max_positions:
            logger.info("Max LT positions reached (%d)", config.lt_max_positions)
            return 0

        # 10% of total capital, split across positions
        lt_budget = int(state.current_balance_cents * config.long_term_allocation)
        remaining_lt = lt_budget - state.lt_deployed_cents
        if remaining_lt <= 0:
            logger.info("LT budget exhausted")
            return 0

        count = remaining_lt // max(opportunity.price_cents, 1)
        return max(0, count)

    return 0


def should_exit_short_term(
    position: Position,
    current_price: int,
    config: Config,
    is_hot: bool,
) -> tuple[bool, str]:
    """Check if a short-term position should be exited.

    Returns (should_exit, reason).
    """
    position.last_price = current_price
    pnl_pct = position.unrealized_pnl_pct

    # Target profit hit
    target = config.hot_state_target_profit_pct if is_hot else config.st_target_profit_pct
    if pnl_pct >= target:
        return True, f"Target profit hit: +{pnl_pct:.2%}"

    # Stop loss
    if pnl_pct <= -config.st_stop_loss_pct:
        return True, f"Stop loss triggered: {pnl_pct:.2%}"

    # Stale position (no movement)
    elapsed_min = (time.time() - position.entry_time) / 60
    price_unchanged = abs(current_price - position.entry_price) <= 1
    if elapsed_min >= config.st_stale_minutes and price_unchanged:
        return True, f"Stale position ({elapsed_min:.0f}min, no movement)"

    return False, ""


def should_exit_long_term(
    position: Position,
    current_price: int,
    config: Config,
) -> tuple[bool, str]:
    """Check if a long-term position should be exited.

    Only exit if: price reaches 97-99 (early exit) or thesis breaks.
    """
    position.last_price = current_price

    if current_price >= config.lt_exit_price:
        return True, f"Early exit: price reached {current_price}c (>={config.lt_exit_price}c)"

    # Thesis break: probability dropped well below entry level
    # If price drops more than 15c from entry, thesis may be broken
    if current_price <= position.entry_price - 15:
        return True, f"Thesis break: price dropped to {current_price}c from {position.entry_price}c entry"

    return False, ""


def record_trade(state: StrategyState) -> None:
    """Increment daily trade counter."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.trade_day != today:
        state.trades_today = 0
        state.trade_day = today
    state.trades_today += 1


def can_trade(state: StrategyState, config: Config) -> tuple[bool, str]:
    """Check if trading is allowed right now."""
    if state.killed:
        return False, "Kill switch active — trading paused"

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.trade_day == today and state.trades_today >= config.max_trades_per_day:
        return False, f"Max trades/day reached ({config.max_trades_per_day})"

    return True, ""


def add_position(
    state: StrategyState,
    ticker: str,
    side: str,
    price_cents: int,
    count: int,
    strategy: str,
) -> Position:
    """Record a new position."""
    cost = price_cents * count
    pos = Position(
        ticker=ticker,
        side=side,
        entry_price=price_cents,
        count=count,
        cost_cents=cost,
        strategy=strategy,
        entry_time=time.time(),
        last_price=price_cents,
    )
    state.positions.append(pos)
    record_trade(state)
    logger.info(
        "Position opened: %s %s %s @ %dc x%d ($%.2f) [%s]",
        strategy, side, ticker, price_cents, count, cost / 100, strategy,
    )
    return pos


def close_position(state: StrategyState, position: Position, exit_price: int) -> int:
    """Close a position and return realized P&L in cents."""
    pnl = (exit_price - position.entry_price) * position.count
    state.session_pnl_cents += pnl
    state.positions.remove(position)
    logger.info(
        "Position closed: %s %s @ %dc (entry %dc) x%d | P&L: %+dc ($%+.2f)",
        position.side, position.ticker, exit_price, position.entry_price,
        position.count, pnl, pnl / 100,
    )
    return pnl


def get_strategy_summary(state: StrategyState, config: Config) -> dict:
    """Get a summary of current strategy state."""
    check_hot_state(state, config)
    return {
        "balance": f"${state.current_balance_cents / 100:.2f}",
        "equity": f"${state.equity_cents / 100:.2f}",
        "peak_equity": f"${state.peak_equity_cents / 100:.2f}",
        "session_pnl": f"{state.session_pnl_pct:+.2%}",
        "drawdown": f"{state.drawdown_from_peak_pct:.2%}",
        "hot_state": state.hot_state_active,
        "killed": state.killed,
        "st_positions": len(state.short_term_positions),
        "lt_positions": len(state.long_term_positions),
        "st_deployed": f"${state.st_deployed_cents / 100:.2f}",
        "lt_deployed": f"${state.lt_deployed_cents / 100:.2f}",
        "trades_today": state.trades_today,
        "max_trades": config.max_trades_per_day,
    }
