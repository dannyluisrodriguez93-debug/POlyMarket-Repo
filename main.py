#!/usr/bin/env python3
"""Kalshi Trading Bot — interactive CLI entry point."""

import sys
import logging

from kalshi_bot.config import Config
from kalshi_bot.client import KalshiClient
from kalshi_bot.market_analyzer import (
    analyze_all,
    search_markets,
    Opportunity,
)
from kalshi_bot.trader import (
    place_limit_order,
    place_market_order,
    get_open_orders,
    cancel_order,
    cancel_all_orders,
)
from kalshi_bot.display import (
    console,
    show_banner,
    show_markets_table,
    show_opportunities,
    show_opportunity_detail,
    prompt_approval,
    show_trade_result,
    show_orders_table,
    show_balance,
    show_error,
    show_info,
    show_success,
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("kalshi_bot")


def cmd_help():
    console.print(
        "\n[bold]Commands:[/bold]\n"
        "  [cyan]markets[/cyan]           — Browse all active markets\n"
        "  [cyan]search <query>[/cyan]    — Search markets by keyword\n"
        "  [cyan]analyze[/cyan]           — Scan for 80%+ probability opportunities\n"
        "  [cyan]opportunities[/cyan]     — Show last analysis results\n"
        "  [cyan]detail <#>[/cyan]        — Show detail for opportunity #\n"
        "  [cyan]buy <#> [count] [price][/cyan] — Place limit buy on opportunity #\n"
        "  [cyan]market-buy <#> [count][/cyan]  — Place market buy on opportunity #\n"
        "  [cyan]orders[/cyan]            — Show open orders\n"
        "  [cyan]cancel <id>[/cyan]       — Cancel an order by ID\n"
        "  [cyan]cancel-all[/cyan]        — Cancel all open orders\n"
        "  [cyan]balance[/cyan]           — Show account balance\n"
        "  [cyan]refresh[/cyan]           — Re-fetch all markets\n"
        "  [cyan]help[/cyan]              — Show this help\n"
        "  [cyan]quit[/cyan]              — Exit the bot\n"
    )


def main():
    show_banner()

    # Load config
    config = Config.from_env()
    errors = config.validate()
    if errors:
        for err in errors:
            show_error(err)
        console.print(
            "\n[dim]Copy .env.example to .env and fill in your credentials.[/dim]"
        )
        sys.exit(1)

    # Connect and authenticate
    show_info("Connecting to Kalshi API...")
    client = KalshiClient(config)
    try:
        if client.login():
            show_success("Authenticated with Kalshi!")
        else:
            show_error("Authentication failed. Check your credentials.")
            sys.exit(1)
    except Exception as e:
        show_error(f"Failed to connect: {e}")
        sys.exit(1)

    # Show balance
    try:
        balance = client.get_balance()
        show_balance(balance)
    except Exception:
        show_info("Could not fetch balance (non-critical).")

    # Fetch markets
    show_info("Fetching all Kalshi markets...")
    markets = client.fetch_all_markets()
    show_success(f"Loaded {len(markets)} open markets.")

    # State
    all_opportunities: list[Opportunity] = []
    market_page = 1

    cmd_help()

    while True:
        try:
            raw = console.input("\n[bold cyan]kalshi>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        # ---- Markets ----
        if cmd == "markets":
            page = int(arg) if arg.isdigit() else market_page
            show_markets_table(markets, page=page)
            market_page = page + 1

        elif cmd == "search":
            if not arg:
                show_error("Usage: search <query>")
                continue
            results = search_markets(markets, arg)
            show_info(f"Found {len(results)} markets matching '{arg}'")
            show_markets_table(results)

        # ---- Analysis ----
        elif cmd == "analyze":
            show_info(f"Scanning for markets with >= {config.min_probability:.0%} probability...")
            results = analyze_all(markets, config.min_probability)
            all_opportunities.clear()

            for strategy_name, opps in results.items():
                all_opportunities.extend(opps)

            show_opportunities(all_opportunities)
            show_success(f"Total opportunities: {len(all_opportunities)}")

        elif cmd == "opportunities":
            if not all_opportunities:
                show_info("No opportunities yet. Run 'analyze' first.")
            else:
                show_opportunities(all_opportunities)

        elif cmd == "detail":
            try:
                idx = int(arg) - 1
                if 0 <= idx < len(all_opportunities):
                    show_opportunity_detail(all_opportunities[idx], idx + 1)
                else:
                    show_error(f"Invalid #. Range: 1-{len(all_opportunities)}")
            except ValueError:
                show_error("Usage: detail <number>")

        # ---- Trading ----
        elif cmd == "buy":
            try:
                buy_parts = arg.split()
                idx = int(buy_parts[0]) - 1
                if not (0 <= idx < len(all_opportunities)):
                    show_error(f"Invalid #. Range: 1-{len(all_opportunities)}")
                    continue

                opp = all_opportunities[idx]
                count = int(buy_parts[1]) if len(buy_parts) > 1 else config.default_order_size
                price_cents = int(buy_parts[2]) if len(buy_parts) > 2 else opp.price_cents

                if count > config.max_order_size:
                    show_error(f"Count {count} exceeds max {config.max_order_size}")
                    continue

                show_opportunity_detail(opp, idx + 1)
                if prompt_approval(opp, count):
                    show_info("Placing limit order...")
                    result = place_limit_order(client, opp, count, price_cents)
                    show_trade_result(result.to_dict())
                else:
                    show_info("Trade cancelled by user.")
            except (ValueError, IndexError):
                show_error("Usage: buy <#> [count] [price_cents]")

        elif cmd == "market-buy":
            try:
                buy_parts = arg.split()
                idx = int(buy_parts[0]) - 1
                if not (0 <= idx < len(all_opportunities)):
                    show_error(f"Invalid #. Range: 1-{len(all_opportunities)}")
                    continue

                opp = all_opportunities[idx]
                count = int(buy_parts[1]) if len(buy_parts) > 1 else config.default_order_size

                if count > config.max_order_size:
                    show_error(f"Count {count} exceeds max {config.max_order_size}")
                    continue

                show_opportunity_detail(opp, idx + 1)
                if prompt_approval(opp, count):
                    show_info("Placing market order...")
                    result = place_market_order(client, opp, count)
                    show_trade_result(result.to_dict())
                else:
                    show_info("Trade cancelled by user.")
            except (ValueError, IndexError):
                show_error("Usage: market-buy <#> [count]")

        # ---- Orders ----
        elif cmd == "orders":
            show_info("Fetching open orders...")
            orders = get_open_orders(client)
            show_orders_table(orders)

        elif cmd == "cancel":
            if not arg:
                show_error("Usage: cancel <order_id>")
                continue
            if cancel_order(client, arg):
                show_success(f"Order {arg} cancelled.")
            else:
                show_error(f"Failed to cancel order {arg}")

        elif cmd == "cancel-all":
            response = console.input("[yellow]Cancel ALL open orders? (y/N): [/yellow]")
            if response.strip().lower() in ("y", "yes"):
                count = cancel_all_orders(client)
                show_success(f"Cancelled {count} orders.")

        # ---- Utility ----
        elif cmd == "balance":
            try:
                balance = client.get_balance()
                show_balance(balance)
            except Exception as e:
                show_error(f"Failed to fetch balance: {e}")

        elif cmd == "refresh":
            show_info("Refreshing markets...")
            markets = client.fetch_all_markets()
            all_opportunities.clear()
            market_page = 1
            show_success(f"Reloaded {len(markets)} markets.")

        elif cmd == "help":
            cmd_help()

        elif cmd in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        else:
            show_error(f"Unknown command: {cmd}. Type 'help' for commands.")


if __name__ == "__main__":
    main()
