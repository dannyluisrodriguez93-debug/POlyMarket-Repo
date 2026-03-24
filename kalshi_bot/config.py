"""Configuration for the Kalshi Trading Bot."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    kalshi_api_url: str = "https://trading-api.kalshi.com/trade-api/v2"
    kalshi_email: str = ""
    kalshi_password: str = ""
    kalshi_api_key_id: str = ""
    kalshi_api_private_key_path: str = ""
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

        if self.default_order_size < 1:
            errors.append("DEFAULT_ORDER_SIZE must be at least 1")
        if self.max_order_size < self.default_order_size:
            errors.append("MAX_ORDER_SIZE must be >= DEFAULT_ORDER_SIZE")
        if not (0.0 < self.min_probability < 1.0):
            errors.append("MIN_PROBABILITY must be between 0.0 and 1.0")

        return errors
