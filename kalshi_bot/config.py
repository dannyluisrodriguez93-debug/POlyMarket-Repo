"""Configuration for the Kalshi Trading Bot."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    # --- API ---
    kalshi_api_url: str = "https://trading-api.kalshi.com/trade-api/v2"
    kalshi_email: str = ""
    kalshi_password: str = ""
    kalshi_api_key_id: str = ""
    kalshi_api_private_key_path: str = ""

    # --- Capital Allocation ---
    short_term_allocation: float = 0.90  # 90% to short-term scalping
    long_term_allocation: float = 0.10   # 10% to long-term holds

    # --- Short-Term Strategy ---
    st_min_probability: float = 0.85     # Primary threshold
    st_momentum_probability: float = 0.80  # Allowed with momentum (80-84%)
    st_max_price: int = 95               # Avoid >0.96
    st_min_volume: int = 5000            # Minimum $5,000 volume
    st_max_spread: float = 0.03          # Max 2-3% spread
    st_max_hours_to_close: int = 24      # Resolution 0-24h
    st_ideal_hours_to_close: int = 12    # Ideal <12h
    st_position_size_pct: float = 0.25   # 20-30% per trade (midpoint)
    st_max_concurrent: int = 4           # Max 2-4 concurrent positions
    st_max_capital_deployed: float = 0.60  # Max 60% capital at risk
    st_target_profit_pct: float = 0.05   # +2% to +8% target (midpoint 5%)
    st_stop_loss_pct: float = 0.05       # -5% move stop loss
    st_stale_minutes: int = 45           # Exit if no movement 30-60 min

    # --- Long-Term Strategy ---
    lt_min_probability: float = 0.90     # 90-95% ONLY
    lt_min_days_to_close: int = 30       # 30-60 day horizon
    lt_max_days_to_close: int = 60
    lt_max_positions: int = 3            # Max 1-3 positions
    lt_min_price: int = 85              # Prefer 0.85-0.95
    lt_max_price: int = 95
    lt_max_spread: float = 0.05          # Spread <=5%
    lt_exit_price: int = 97              # Early exit at 0.97-0.99

    # --- Hot State (Adaptive Mode) ---
    hot_state_trigger_pct: float = 0.10  # Triggered at +10% PnL
    hot_state_max_trigger_pct: float = 0.25  # Up to +25% PnL
    hot_state_position_size_pct: float = 0.60  # 50-70% size (midpoint)
    hot_state_min_probability: float = 0.88  # Only 88-90%+ trades
    hot_state_target_profit_pct: float = 0.025  # +1% to +4% (midpoint)

    # --- Kill Switch ---
    kill_switch_drawdown_pct: float = 0.05  # Pause at -5% from peak equity

    # --- Trade Frequency ---
    max_trades_per_day: int = 10
    min_trades_per_day: int = 3

    # --- Legacy (kept for compatibility) ---
    default_order_size: int = 10
    max_order_size: int = 100
    min_probability: float = 0.80

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            kalshi_api_url=os.getenv("KALSHI_API_URL", "https://trading-api.kalshi.com/trade-api/v2"),
            kalshi_email=os.getenv("KALSHI_EMAIL", ""),
            kalshi_password=os.getenv("KALSHI_PASSWORD", ""),
            kalshi_api_key_id=os.getenv("KALSHI_API_KEY_ID", ""),
            kalshi_api_private_key_path=os.getenv("KALSHI_API_PRIVATE_KEY_PATH", ""),
            short_term_allocation=float(os.getenv("SHORT_TERM_ALLOCATION", "0.90")),
            long_term_allocation=float(os.getenv("LONG_TERM_ALLOCATION", "0.10")),
            st_min_probability=float(os.getenv("ST_MIN_PROBABILITY", "0.85")),
            st_momentum_probability=float(os.getenv("ST_MOMENTUM_PROBABILITY", "0.80")),
            st_max_price=int(os.getenv("ST_MAX_PRICE", "95")),
            st_min_volume=int(os.getenv("ST_MIN_VOLUME", "5000")),
            st_max_hours_to_close=int(os.getenv("ST_MAX_HOURS_TO_CLOSE", "24")),
            st_ideal_hours_to_close=int(os.getenv("ST_IDEAL_HOURS_TO_CLOSE", "12")),
            st_position_size_pct=float(os.getenv("ST_POSITION_SIZE_PCT", "0.25")),
            st_max_concurrent=int(os.getenv("ST_MAX_CONCURRENT", "4")),
            st_max_capital_deployed=float(os.getenv("ST_MAX_CAPITAL_DEPLOYED", "0.60")),
            st_target_profit_pct=float(os.getenv("ST_TARGET_PROFIT_PCT", "0.05")),
            st_stop_loss_pct=float(os.getenv("ST_STOP_LOSS_PCT", "0.05")),
            st_stale_minutes=int(os.getenv("ST_STALE_MINUTES", "45")),
            lt_min_probability=float(os.getenv("LT_MIN_PROBABILITY", "0.90")),
            lt_min_days_to_close=int(os.getenv("LT_MIN_DAYS_TO_CLOSE", "30")),
            lt_max_days_to_close=int(os.getenv("LT_MAX_DAYS_TO_CLOSE", "60")),
            lt_max_positions=int(os.getenv("LT_MAX_POSITIONS", "3")),
            lt_min_price=int(os.getenv("LT_MIN_PRICE", "85")),
            lt_max_price=int(os.getenv("LT_MAX_PRICE", "95")),
            lt_exit_price=int(os.getenv("LT_EXIT_PRICE", "97")),
            hot_state_trigger_pct=float(os.getenv("HOT_STATE_TRIGGER_PCT", "0.10")),
            hot_state_max_trigger_pct=float(os.getenv("HOT_STATE_MAX_TRIGGER_PCT", "0.25")),
            hot_state_position_size_pct=float(os.getenv("HOT_STATE_POSITION_SIZE_PCT", "0.60")),
            hot_state_min_probability=float(os.getenv("HOT_STATE_MIN_PROBABILITY", "0.88")),
            hot_state_target_profit_pct=float(os.getenv("HOT_STATE_TARGET_PROFIT_PCT", "0.025")),
            kill_switch_drawdown_pct=float(os.getenv("KILL_SWITCH_DRAWDOWN_PCT", "0.05")),
            max_trades_per_day=int(os.getenv("MAX_TRADES_PER_DAY", "10")),
            default_order_size=int(os.getenv("DEFAULT_ORDER_SIZE", "10")),
            max_order_size=int(os.getenv("MAX_ORDER_SIZE", "100")),
            min_probability=float(os.getenv("MIN_PROBABILITY", "0.80")),
        )

    def validate(self) -> list[str]:
        errors = []
        has_email_auth = self.kalshi_email and self.kalshi_password
        has_api_key_auth = self.kalshi_api_key_id and self.kalshi_api_private_key_path

        if not has_email_auth and not has_api_key_auth:
            errors.append("Provide either (KALSHI_EMAIL + KALSHI_PASSWORD) or (KALSHI_API_KEY_ID + KALSHI_API_PRIVATE_KEY_PATH)")

        if has_api_key_auth and self.kalshi_api_private_key_path:
            if not os.path.exists(self.kalshi_api_private_key_path):
                errors.append(f"Private key file not found: {self.kalshi_api_private_key_path}")

        if not (0.0 < self.short_term_allocation + self.long_term_allocation <= 1.0):
            errors.append("SHORT_TERM_ALLOCATION + LONG_TERM_ALLOCATION must be <= 1.0")

        if self.default_order_size < 1:
            errors.append("DEFAULT_ORDER_SIZE must be at least 1")
        if self.max_order_size < self.default_order_size:
            errors.append("MAX_ORDER_SIZE must be >= DEFAULT_ORDER_SIZE")

        return errors
