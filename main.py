#!/usr/bin/env python3
"""Polymarket Trading Bot — interactive CLI entry point."""

import sys
import logging

from polymarket_bot.config import Config
from polymarket_bot.client import create_client, fetch_all_markets
from polymarket_bot.market_analyzer import (
    analyze_all,
    search_markets,
    get_market_details,
    Opportunity,
)
from polymarket_bot.trader import (
    place_limit_order,
    place_market_order,
    get_open_orders,
    cancel_order,
    cancel_all_orders,
)
from polymarket_bot.display import (
    console,
    show_banner,
    show_markets_table,
    show_opportunities,
    show_opportunity_detail,
    prompt_approval,
    show_trade_result,
    show_orders_table,
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
logger = logging.getLogger("polymarket_bot")


def cmd_help():
    console.print(
        "\n[bold]Commands:[/bold]\n"
        "  [cyan]markets[/cyan]           — Browse all active markets\n"
        "  [cyan]search <query>[/cyan]    — Search markets by keyword\n"
        "  [cyan]analyze[/cyan]           — Run all analysis strategies\n"
        "  [cyan]opportunities[/cyan]     — Show last analysis results\n"
        "  [cyan]detail <#>[/cyan]        — Show detail for opportunity #\n"
        "  [cyan]buy <#> [size] [price][/cyan] — Place limit buy on opportunity #\n"
        "  [cyan]market-buy <#> [amount][/cyan] — Place market buy on opportunity #\n"
        "  [cyan]orders[/cyan]            — Show open orders\n"
        "  [cyan]cancel <id>[/cyan]       — Cancel an order by ID\n"
        "  [cyan]cancel-all[/cyan]        — Cancel all open orders\n"
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

    # Connect
    show_info("Connecting to Polymarket CLOB API...")
    try:
        client = create_client(config)
        ok = client.get_ok()
        show_success(f"Connected! Server status: {ok}")
    except Exception as e:
        show_error(f"Failed to connect: {e}")
        sys.exit(1)

    # Fetch markets
    show_info("Fetching markets...")
    markets = fetch_all_markets(client)
    show_success(f"Loaded {len(markets)} markets.")

    # State
    all_opportunities: list[Opportunity] = []
    market_page = 0

    cmd_help()

    while True:
        try:
            raw = console.input("\n[bold cyan]bot>[/bold cyan] ").strip()
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
            has_more = show_markets_table(markets, market_page)
            if has_more:
                console.print("[dim]Type 'markets' again for next page, or 'search <query>'[/dim]")
                market_page += 1
            else:
                market_page = 0

        elif cmd == "search":
            if not arg:
                show_error("Usage: search <query>")
                continue
            results = search_markets(markets, arg)
            show_info(f"Found {len(results)} markets matching '{arg}'")
            show_markets_table(results)

        # ---- Analysis ----
        elif cmd == "analyze":
            show_info("Analyzing markets...")
            results = analyze_all(client, markets)
            all_opportunities.clear()

            for strategy_name, opps in results.items():
                show_opportunities(opps, strategy_name.replace("_", " ").title())
                all_opportunities.extend(opps)

            show_success(f"Total opportunities: {len(all_opportunities)}")

        elif cmd == "opportunities":
            if not all_opportunities:
                show_info("No opportunities yet. Run 'analyze' first.")
            else:
                show_opportunities(all_opportunities, "All")

        elif cmd == "detail":
            try:
                idx = int(arg) - 1
                if 0 <= idx < len(all_opportunities):
                    show_opportunity_detail(all_opportunities[idx])
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
                size = float(buy_parts[1]) if len(buy_parts) > 1 else config.default_order_size
                price = float(buy_parts[2]) if len(buy_parts) > 2 else opp.current_price

                if size > config.max_order_size:
                    show_error(f"Size {size} exceeds max {config.max_order_size}")
                    continue

                show_opportunity_detail(opp)
                if prompt_approval(opp, size, price, "LIMIT"):
                    show_info("Placing limit order...")
                    result = place_limit_order(client, opp, size, price)
                    show_trade_result(result)
                else:
                    show_info("Trade cancelled by user.")
            except (ValueError, IndexError):
                show_error("Usage: buy <#> [size] [price]")

        elif cmd == "market-buy":
            try:
                buy_parts = arg.split()
                idx = int(buy_parts[0]) - 1
                if not (0 <= idx < len(all_opportunities)):
                    show_error(f"Invalid #. Range: 1-{len(all_opportunities)}")
                    continue

                opp = all_opportunities[idx]
                amount = float(buy_parts[1]) if len(buy_parts) > 1 else config.default_order_size

                if amount > config.max_order_size:
                    show_error(f"Amount {amount} exceeds max {config.max_order_size}")
                    continue

                show_opportunity_detail(opp)
                if prompt_approval(opp, amount, opp.current_price, "MARKET"):
                    show_info("Placing market order...")
                    result = place_market_order(client, opp, amount)
                    show_trade_result(result)
                else:
                    show_info("Trade cancelled by user.")
            except (ValueError, IndexError):
                show_error("Usage: market-buy <#> [amount]")

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
                if cancel_all_orders(client):
                    show_success("All orders cancelled.")
                else:
                    show_error("Failed to cancel all orders.")

        # ---- Utility ----
        elif cmd == "refresh":
            show_info("Refreshing markets...")
            markets = fetch_all_markets(client)
            all_opportunities.clear()
            market_page = 0
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
