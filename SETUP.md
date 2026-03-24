# Polymarket Trading Bot — Setup Guide

## 1. Create a Polymarket Account

1. Go to [polymarket.com](https://polymarket.com)
2. Click "Sign Up" and connect your wallet (MetaMask, WalletConnect, etc.)
3. Complete any required identity verification
4. Deposit USDC on the Polygon network to your Polymarket wallet

## 2. Get Your API Credentials

The bot needs your **private key** to sign orders. Your CLOB API credentials
are derived automatically from your private key.

**Option A: Use your wallet's private key**
- Export your private key from MetaMask (Account Details → Export Private Key)
- This is the same wallet you use on Polymarket

**Option B: Generate a dedicated trading wallet**
- Create a new wallet for bot trading
- Fund it with MATIC (gas) and USDC (trading) on Polygon
- Transfer funds from your main Polymarket wallet

## 3. Configure the Bot

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
PRIVATE_KEY=your_hex_private_key_without_0x_prefix
```

The bot will auto-derive your CLOB API key, secret, and passphrase.

### Optional settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLOB_API_URL` | `https://clob.polymarket.com` | CLOB API endpoint |
| `CHAIN_ID` | `137` | Polygon mainnet |
| `DEFAULT_ORDER_SIZE` | `5.00` | Default trade size in USDC |
| `MAX_ORDER_SIZE` | `50.00` | Max allowed trade size |
| `SLIPPAGE_TOLERANCE` | `0.02` | Max slippage for market orders |

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Run the Bot

```bash
python main.py
```

## 6. Bot Commands

| Command | Description |
|---------|-------------|
| `markets` | Browse all active markets (paginated) |
| `search <query>` | Search markets by keyword |
| `analyze` | Run all analysis strategies |
| `opportunities` | Show last analysis results |
| `detail <#>` | Show detailed view of opportunity |
| `buy <#> [size] [price]` | Place limit buy order |
| `market-buy <#> [amount]` | Place market buy order |
| `orders` | Show open orders |
| `cancel <id>` | Cancel a specific order |
| `cancel-all` | Cancel all open orders |
| `refresh` | Re-fetch all markets |
| `help` | Show available commands |
| `quit` | Exit |

## Trading Strategies

The bot includes three built-in analysis strategies:

### Arbitrage Detection
Finds binary markets where Yes + No prices don't sum to ~1.0. If the sum is
less than 0.98, buying both outcomes guarantees a profit.

### Undervalued Longshots
Finds outcomes priced below $0.30 (configurable). These have high potential
returns if they win, though they're considered less likely by the market.

### Wide Spread Market Making
Finds markets with wide bid-ask spreads (>3%). You can place orders on both
sides to capture the spread.

## Important Notes

- **All trades require your explicit approval** — the bot never auto-executes
- **Start small** — use small order sizes while testing
- **Monitor your positions** — use `orders` to track open orders
- **USDC is required** — ensure your wallet has USDC on Polygon
- **MATIC for gas** — keep a small MATIC balance for transaction fees
