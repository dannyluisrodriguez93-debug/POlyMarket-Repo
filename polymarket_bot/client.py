"""CLOB client wrapper — handles connection, authentication, and API calls."""

import logging
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

from .config import Config

logger = logging.getLogger(__name__)


def create_client(config: Config) -> ClobClient:
    """Create and authenticate a ClobClient instance."""
    creds = None
    if config.clob_api_key and config.clob_api_secret and config.clob_api_passphrase:
        creds = ApiCreds(
            api_key=config.clob_api_key,
            api_secret=config.clob_api_secret,
            api_passphrase=config.clob_api_passphrase,
        )

    client = ClobClient(
        host=config.clob_api_url,
        chain_id=config.chain_id,
        key=config.private_key,
        creds=creds,
    )

    # If no creds provided, derive them
    if creds is None and config.private_key:
        logger.info("Deriving API credentials from private key...")
        derived_creds = client.create_or_derive_api_creds()
        if derived_creds:
            client.set_api_creds(derived_creds)
            logger.info("API credentials set successfully.")
        else:
            logger.warning("Could not derive API credentials. Read-only mode.")

    return client


def fetch_all_markets(client: ClobClient) -> list[dict]:
    """Fetch all active markets with pagination."""
    all_markets = []
    cursor = "MA=="

    while True:
        response = client.get_markets(next_cursor=cursor)
        data = response if isinstance(response, list) else response.get("data", [])
        next_cursor = (
            response.get("next_cursor", "MA==")
            if isinstance(response, dict)
            else "MA=="
        )

        if not data:
            break

        all_markets.extend(data)

        if next_cursor == "MA==" or next_cursor == cursor:
            break
        cursor = next_cursor

    logger.info("Fetched %d markets.", len(all_markets))
    return all_markets
