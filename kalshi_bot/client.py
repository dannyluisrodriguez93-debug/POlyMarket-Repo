"""Kalshi REST API client."""

import base64
import hashlib
import logging
import time
from datetime import datetime, timezone

import requests

from .config import Config

logger = logging.getLogger("kalshi_bot")


class KalshiClient:
    """Client for interacting with the Kalshi trading API."""

    def __init__(self, config: Config):
        self.base_url = config.kalshi_api_url.rstrip("/")
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self._token: str | None = None
        self._private_key = None

    def login(self) -> bool:
        """Authenticate with Kalshi. Returns True on success."""
        if self.config.kalshi_email and self.config.kalshi_password:
            return self._login_email()
        elif self.config.kalshi_api_key_id and self.config.kalshi_api_private_key_path:
            return self._setup_api_key_auth()
        else:
            raise ValueError("No authentication credentials configured")

    def _login_email(self) -> bool:
        """Login with email and password."""
        resp = self.session.post(
            f"{self.base_url}/login",
            json={"email": self.config.kalshi_email, "password": self.config.kalshi_password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data.get("token")
        if self._token:
            self.session.headers["Authorization"] = f"Bearer {self._token}"
            return True
        return False

    def _setup_api_key_auth(self) -> bool:
        """Configure RSA API key authentication."""
        try:
            from cryptography.hazmat.primitives import serialization

            with open(self.config.kalshi_api_private_key_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(f.read(), password=None)
            # Verify by fetching balance
            self._make_signed_request("GET", "/portfolio/balance")
            return True
        except Exception as e:
            logger.error("API key auth failed: %s", e)
            return False

    def _sign_request(self, method: str, path: str, timestamp_ms: int) -> str:
        """Create RSA-PSS signature for API key auth."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        message = f"{timestamp_ms}{method}{path}".encode()
        signature = self._private_key.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def _make_signed_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make a request signed with the API key."""
        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        signature = self._sign_request(method, path, timestamp_ms)

        headers = {
            "KALSHI-ACCESS-KEY": self.config.kalshi_api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
        }
        resp = self.session.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make an authenticated request, choosing the right auth method."""
        if self._private_key:
            return self._make_signed_request(method, path, **kwargs)
        resp = self.session.request(method, f"{self.base_url}{path}", **kwargs)
        resp.raise_for_status()
        return resp

    def fetch_all_markets(self) -> list[dict]:
        """Fetch all active markets with pagination."""
        all_markets = []
        cursor = None

        while True:
            params = {"limit": 200, "status": "open"}
            if cursor:
                params["cursor"] = cursor

            resp = self._request("GET", "/markets", params=params)
            data = resp.json()

            markets = data.get("markets", [])
            if not markets:
                break

            all_markets.extend(markets)
            cursor = data.get("cursor")

            if not cursor:
                break

            # Rate limit: small delay between pages
            time.sleep(0.1)
            logger.info("Fetched %d markets so far...", len(all_markets))

        logger.info("Total markets fetched: %d", len(all_markets))
        return all_markets

    def get_market(self, ticker: str) -> dict:
        """Get details for a single market."""
        resp = self._request("GET", f"/markets/{ticker}")
        return resp.json().get("market", resp.json())

    def get_balance(self) -> dict:
        """Get portfolio balance."""
        resp = self._request("GET", "/portfolio/balance")
        return resp.json()

    def place_order(
        self,
        ticker: str,
        side: str,
        action: str = "buy",
        count: int = 1,
        order_type: str = "limit",
        yes_price: int | None = None,
        no_price: int | None = None,
    ) -> dict:
        """Place an order on a market.

        Args:
            ticker: Market ticker.
            side: 'yes' or 'no'.
            action: 'buy' or 'sell'.
            count: Number of contracts.
            order_type: 'limit' or 'market'.
            yes_price: Price in cents (1-99) for limit orders.
            no_price: Price in cents (1-99) for limit orders.
        """
        body: dict = {
            "ticker": ticker,
            "action": action,
            "side": side,
            "count": count,
            "type": order_type,
        }
        if yes_price is not None:
            body["yes_price"] = yes_price
        if no_price is not None:
            body["no_price"] = no_price

        resp = self._request("POST", "/portfolio/orders", json=body)
        return resp.json()

    def get_orders(self, status: str | None = None) -> list[dict]:
        """Get orders, optionally filtered by status."""
        params = {}
        if status:
            params["status"] = status
        resp = self._request("GET", "/portfolio/orders", params=params)
        return resp.json().get("orders", [])

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a specific order."""
        resp = self._request("DELETE", f"/portfolio/orders/{order_id}")
        return resp.status_code in (200, 204)

    def get_events(self, cursor: str | None = None, limit: int = 200) -> dict:
        """Fetch events."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = self._request("GET", "/events", params=params)
        return resp.json()
