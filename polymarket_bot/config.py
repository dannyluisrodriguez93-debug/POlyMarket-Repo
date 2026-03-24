"""Configuration management — loads settings from environment variables."""

import os
import sys
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class Config:
    clob_api_url: str = "https://clob.polymarket.com"
    chain_id: int = 137
    private_key: str = ""
    clob_api_key: str = ""
    clob_api_secret: str = ""
    clob_api_passphrase: str = ""
    default_order_size: float = 5.00
    max_order_size: float = 50.00
    slippage_tolerance: float = 0.02

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            clob_api_url=os.getenv("CLOB_API_URL", "https://clob.polymarket.com"),
            chain_id=int(os.getenv("CHAIN_ID", "137")),
            private_key=os.getenv("PRIVATE_KEY", ""),
            clob_api_key=os.getenv("CLOB_API_KEY", ""),
            clob_api_secret=os.getenv("CLOB_API_SECRET", ""),
            clob_api_passphrase=os.getenv("CLOB_API_PASSPHRASE", ""),
            default_order_size=float(os.getenv("DEFAULT_ORDER_SIZE", "5.00")),
            max_order_size=float(os.getenv("MAX_ORDER_SIZE", "50.00")),
            slippage_tolerance=float(os.getenv("SLIPPAGE_TOLERANCE", "0.02")),
        )

    def validate(self) -> list[str]:
        errors = []
        if not self.private_key:
            errors.append("PRIVATE_KEY is required")
        if self.max_order_size <= 0:
            errors.append("MAX_ORDER_SIZE must be positive")
        if not 0 <= self.slippage_tolerance <= 1:
            errors.append("SLIPPAGE_TOLERANCE must be between 0 and 1")
        return errors
