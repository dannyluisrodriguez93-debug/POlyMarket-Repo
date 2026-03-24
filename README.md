# Kalshi Trading Bot

An interactive CLI trading bot for the [Kalshi](https://kalshi.com) prediction market platform. It uses a **dual-strategy engine** — 90% short-term scalping and 10% long-term holds — to find and execute high-probability trades.

## Features

- **Dual-Strategy Engine** — Splits capital between fast short-term scalps and patient long-term holds
- **Market Scanner** — Scans all active Kalshi markets for opportunities based on probability, volume, and time-to-close
- **Adaptive "Hot State"** — Automatically increases position sizes during winning streaks
- **Kill Switch** — Halts trading if drawdown exceeds a configurable threshold
- **Position Sizing** — Auto-calculates order size based on strategy, capital allocation, and risk limits
- **Interactive CLI** — Rich terminal UI with tables, color-coded output, and manual trade approval
- **No Auto-Execution** — Every trade requires explicit user approval before placing

## Project Structure

```
├── main.py                  # Entry point and interactive REPL
├── kalshi_bot/
│   ├── client.py            # Kalshi API client (auth, markets, orders)
│   ├── config.py            # Configuration from environment variables
│   ├── market_analyzer.py   # Market scanning and opportunity detection
│   ├── strategy.py          # Dual-strategy state machine and position sizing
│   ├── trader.py            # Order placement (limit and market orders)
│   └── display.py           # Rich terminal UI (tables, banners, prompts)
├── .env.example             # Sample configuration
├── requirements.txt         # Python dependencies
└── SETUP.md                 # Detailed setup guide
```

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url>
cd POlyMarket-Repo
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your Kalshi credentials (email/password or API key).

### 3. Run

```bash
python main.py
```

## Commands

| Command | Description |
|---------|-------------|
| `analyze` | Scan for short-term and long-term opportunities |
| `analyze-st` | Short-term opportunities only |
| `analyze-lt` | Long-term opportunities only |
| `opportunities` | Show last analysis results |
| `detail <#>` | Show detailed view of an opportunity |
| `search <query>` | Search markets by keyword |
| `markets` | Browse all active markets (paginated) |
| `buy <#> [count] [price]` | Place a limit buy order |
| `market-buy <#> [count]` | Place a market buy order |
| `size <#>` | Calculate position size for an opportunity |
| `status` | Show strategy dashboard |
| `positions` | Show active positions |
| `orders` | Show open orders |
| `cancel <id>` | Cancel an order |
| `cancel-all` | Cancel all open orders |
| `balance` | Show account balance |
| `refresh` | Re-fetch all markets |
| `reset-kill` | Reset the kill switch |
| `help` | Show available commands |
| `quit` | Exit the bot |

## Strategy Overview

### Short-Term Scalping (90% of capital)

Targets markets closing within 24 hours with high probability (85%+). Aims for quick 5% profit with a 5% stop-loss. Up to 4 concurrent positions, max 60% capital deployed.

### Long-Term Holds (10% of capital)

Targets markets closing in 30–60 days with very high probability (90%+). Buys between 85–95 cents and exits at 97 cents. Maximum 3 positions.

### Adaptive Hot State

When equity gains exceed 10% from the starting balance, the bot enters "hot state" — increasing position sizes and tightening profit targets to compound gains faster.

### Kill Switch

If equity drops more than 5% from its peak, all trading is halted until manually reset with `reset-kill`.

## Configuration

All strategy parameters are configurable via `.env`. See [`.env.example`](.env.example) for the full list of options including allocation percentages, probability thresholds, position limits, and risk parameters.

## Requirements

- Python 3.10+
- A funded [Kalshi](https://kalshi.com) account
- Dependencies: `requests`, `python-dotenv`, `rich`, `cryptography`

## Disclaimer

This bot is for educational and personal use. Trading on prediction markets involves risk. Always start with small positions and monitor your trades. The authors are not responsible for any financial losses.
