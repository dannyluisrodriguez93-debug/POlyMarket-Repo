"""Rich terminal display for the Kalshi Trading Bot."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .market_analyzer import Opportunity

console = Console()


def show_banner():
    """Display the welcome banner."""
    banner = Text()
    banner.append("KALSHI TRADING BOT", style="bold cyan")
    banner.append("\n")
    banner.append("Fast Compounding + Long-Term Allocation Engine", style="dim")
    banner.append("\n")
    banner.append("90% Scalping | 10% Long-Term Holds | Kill Switch Protected", style="dim italic")
    console.print(Panel(banner, border_style="cyan", padding=(1, 2)))


def show_markets_table(markets: list[dict], page: int = 1, page_size: int = 20):
    """Display markets in a paginated table."""
    start = (page - 1) * page_size
    end = start + page_size
    page_markets = markets[start:end]
    total_pages = (len(markets) + page_size - 1) // page_size

    table = Table(
        title=f"Kalshi Markets (Page {page}/{total_pages} -- {len(markets)} total)",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=5)
    table.add_column("Ticker", style="cyan", max_width=25)
    table.add_column("Title", style="white", max_width=50)
    table.add_column("Yes", justify="right", style="green")
    table.add_column("No", justify="right", style="red")
    table.add_column("Close Date", style="dim", max_width=20)
    table.add_column("Status", style="yellow")

    for i, m in enumerate(page_markets, start=start + 1):
        yes_price = m.get("yes_price", "--")
        no_price = m.get("no_price", "--")
        if isinstance(yes_price, (int, float)):
            yes_display = f"{yes_price}c"
        else:
            yes_display = str(yes_price)
        if isinstance(no_price, (int, float)):
            no_display = f"{no_price}c"
        else:
            no_display = str(no_price)

        close_time = m.get("close_time", m.get("expiration_time", "--"))
        if isinstance(close_time, str) and len(close_time) > 16:
            close_time = close_time[:16]

        table.add_row(
            str(i),
            m.get("ticker", "--"),
            m.get("title", "--"),
            yes_display,
            no_display,
            close_time,
            m.get("status", "--"),
        )

    console.print(table)


def show_opportunities(opportunities: list[Opportunity], strategy_filter: str | None = None):
    """Display opportunities in a table, optionally filtered by strategy."""
    filtered = opportunities
    if strategy_filter:
        filtered = [o for o in opportunities if o.strategy == strategy_filter]

    if not filtered:
        label = strategy_filter or "any"
        console.print(f"[yellow]No {label} opportunities found.[/yellow]")
        return

    label = {
        "short_term": "Short-Term (Scalping)",
        "long_term": "Long-Term (Holds)",
    }.get(strategy_filter, "All")

    table = Table(
        title=f"{label} Opportunities ({len(filtered)} found)",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=5)
    table.add_column("Market", style="white", max_width=40)
    table.add_column("Side", style="bold", width=5)
    table.add_column("Prob", justify="right", style="cyan", width=6)
    table.add_column("Price", justify="right", style="green", width=6)
    table.add_column("Return", justify="right", style="yellow", width=7)
    table.add_column("Hrs/Days", justify="right", style="magenta", width=8)
    table.add_column("Type", style="dim", width=6)
    table.add_column("Conf", style="bold", width=6)

    for i, opp in enumerate(filtered, 1):
        side_style = "green" if opp.outcome == "yes" else "red"
        conf_style = "bold green" if opp.confidence == "HIGH" else "bold yellow"

        if opp.strategy == "long_term":
            time_display = f"{opp.hours_to_close / 24:.0f}d"
        else:
            time_display = f"{opp.hours_to_close:.1f}h"

        type_display = "ST" if opp.strategy == "short_term" else "LT"

        table.add_row(
            str(i),
            opp.market_title[:40],
            Text(opp.outcome.upper(), style=side_style),
            f"{opp.probability:.0%}",
            f"{opp.price_cents}c",
            f"{opp.expected_return:.1f}%",
            time_display,
            type_display,
            Text(opp.confidence, style=conf_style),
        )

    console.print(table)


def show_opportunity_detail(opp: Opportunity, index: int):
    """Display detailed info for a single opportunity."""
    detail = Text()
    detail.append(f"#{index} ", style="dim")
    detail.append(opp.market_title, style="bold white")
    detail.append(f"\n\nTicker: ", style="dim")
    detail.append(opp.ticker, style="cyan")
    detail.append(f"\nEvent: ", style="dim")
    detail.append(opp.event_ticker, style="cyan")
    detail.append(f"\nSide: ", style="dim")
    side_style = "bold green" if opp.outcome == "yes" else "bold red"
    detail.append(opp.outcome.upper(), style=side_style)
    detail.append(f"\nProbability: ", style="dim")
    detail.append(f"{opp.probability:.0%}", style="bold cyan")
    detail.append(f"\nPrice: ", style="dim")
    detail.append(f"{opp.price_cents} cents", style="bold green")
    detail.append(f"\nExpected Return: ", style="dim")
    detail.append(f"{opp.expected_return:.1f}%", style="bold yellow")
    detail.append(f"\nStrategy: ", style="dim")
    strat_label = "Short-Term Scalp" if opp.strategy == "short_term" else "Long-Term Hold"
    detail.append(strat_label, style="bold magenta")
    detail.append(f"\nConfidence: ", style="dim")
    detail.append(opp.confidence, style="bold green" if opp.confidence == "HIGH" else "bold yellow")
    detail.append(f"\nTime to Close: ", style="dim")
    if opp.strategy == "long_term":
        detail.append(f"{opp.hours_to_close / 24:.0f} days", style="white")
    else:
        detail.append(f"{opp.hours_to_close:.1f} hours", style="white")
    detail.append(f"\nClose Time: ", style="dim")
    detail.append(opp.close_time, style="white")
    detail.append(f"\nVolume: ", style="dim")
    detail.append(f"${opp.volume:,}", style="white")
    detail.append(f"\n\nReasoning: ", style="dim")
    detail.append(opp.reasoning, style="italic")

    console.print(Panel(detail, title="Opportunity Detail", border_style="cyan", padding=(1, 2)))


def show_strategy_status(summary: dict):
    """Display current strategy state."""
    hot = "[bold red]ACTIVE[/bold red]" if summary["hot_state"] else "[dim]inactive[/dim]"
    killed = "[bold red]TRIGGERED[/bold red]" if summary["killed"] else "[bold green]OK[/bold green]"

    text = Text()
    text.append("Strategy Dashboard", style="bold cyan")

    panel_content = (
        f"[bold]Balance:[/bold]      {summary['balance']}\n"
        f"[bold]Equity:[/bold]       {summary['equity']}\n"
        f"[bold]Peak Equity:[/bold]  {summary['peak_equity']}\n"
        f"[bold]Session P&L:[/bold]  {summary['session_pnl']}\n"
        f"[bold]Drawdown:[/bold]     {summary['drawdown']}\n"
        f"\n"
        f"[bold]Hot State:[/bold]    {hot}\n"
        f"[bold]Kill Switch:[/bold]  {killed}\n"
        f"\n"
        f"[bold]ST Positions:[/bold] {summary['st_positions']} (deployed: {summary['st_deployed']})\n"
        f"[bold]LT Positions:[/bold] {summary['lt_positions']} (deployed: {summary['lt_deployed']})\n"
        f"[bold]Trades Today:[/bold] {summary['trades_today']}/{summary['max_trades']}"
    )

    console.print(Panel(panel_content, title="Strategy Dashboard", border_style="cyan", padding=(1, 2)))


def show_position_table(positions: list, strategy_filter: str | None = None):
    """Display active positions."""
    filtered = positions
    if strategy_filter:
        filtered = [p for p in positions if p.strategy == strategy_filter]

    if not filtered:
        console.print("[yellow]No active positions.[/yellow]")
        return

    table = Table(title="Active Positions", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Ticker", style="cyan", max_width=20)
    table.add_column("Side", style="bold", width=5)
    table.add_column("Entry", justify="right", style="green", width=7)
    table.add_column("Current", justify="right", style="yellow", width=7)
    table.add_column("Count", justify="right", width=6)
    table.add_column("Cost", justify="right", style="dim", width=8)
    table.add_column("P&L", justify="right", width=8)
    table.add_column("Type", style="dim", width=5)

    for i, pos in enumerate(filtered, 1):
        side_style = "green" if pos.side == "yes" else "red"
        pnl = pos.unrealized_pnl_cents
        pnl_style = "bold green" if pnl >= 0 else "bold red"
        type_display = "ST" if pos.strategy == "short_term" else "LT"

        table.add_row(
            str(i),
            pos.ticker,
            Text(pos.side.upper(), style=side_style),
            f"{pos.entry_price}c",
            f"{pos.last_price}c",
            str(pos.count),
            f"${pos.cost_cents / 100:.2f}",
            Text(f"${pnl / 100:+.2f}", style=pnl_style),
            type_display,
        )

    console.print(table)


def prompt_approval(opp: Opportunity, count: int) -> bool:
    """Ask user to confirm a trade."""
    cost_dollars = count * opp.price_cents / 100
    potential_profit = count * (100 - opp.price_cents) / 100

    strat_label = "SHORT-TERM SCALP" if opp.strategy == "short_term" else "LONG-TERM HOLD"

    console.print(f"\n[bold]Trade Confirmation ({strat_label}):[/bold]")
    console.print(f"  Market: {opp.market_title}")
    console.print(f"  Side:   {opp.outcome.upper()} at {opp.price_cents}c")
    console.print(f"  Count:  {count} contracts")
    console.print(f"  Cost:   ${cost_dollars:.2f}")
    console.print(f"  Profit: ${potential_profit:.2f} if correct ({opp.expected_return:.1f}% return)")
    console.print()

    answer = console.input("[bold yellow]Confirm trade? (yes/no): [/bold yellow]").strip().lower()
    return answer in ("yes", "y")


def show_sizing_info(count: int, opp: Opportunity, is_hot: bool):
    """Show position sizing calculation result."""
    cost = count * opp.price_cents / 100
    mode = "[bold red]HOT STATE[/bold red]" if is_hot else "[dim]normal[/dim]"
    console.print(
        f"  [dim]Calculated size:[/dim] {count} contracts @ {opp.price_cents}c = "
        f"${cost:.2f} | Mode: {mode}"
    )


def show_trade_result(result: dict):
    """Display trade execution result."""
    if result.get("success"):
        console.print(Panel(
            f"[bold green]Order placed successfully![/bold green]\n"
            f"Order ID: {result.get('order_id', '--')}\n"
            f"Status: {result.get('status', '--')}",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]Order failed[/bold red]\n"
            f"Error: {result.get('error', 'Unknown error')}",
            border_style="red",
        ))


def show_orders_table(orders: list[dict]):
    """Display open orders."""
    if not orders:
        console.print("[yellow]No open orders.[/yellow]")
        return

    table = Table(title="Open Orders", show_lines=True)
    table.add_column("#", style="dim", width=5)
    table.add_column("Order ID", style="cyan", max_width=20)
    table.add_column("Ticker", style="white", max_width=20)
    table.add_column("Side", style="bold", width=5)
    table.add_column("Price", justify="right", style="green")
    table.add_column("Count", justify="right", style="yellow")
    table.add_column("Remaining", justify="right", style="dim")
    table.add_column("Status", style="cyan")

    for i, order in enumerate(orders, 1):
        side = order.get("side", "--")
        side_style = "green" if side == "yes" else "red"
        table.add_row(
            str(i),
            order.get("order_id", "--")[:20],
            order.get("ticker", "--"),
            Text(side.upper(), style=side_style),
            f"{order.get('yes_price', order.get('no_price', '--'))}c",
            str(order.get("count", "--")),
            str(order.get("remaining_count", "--")),
            order.get("status", "--"),
        )

    console.print(table)


def show_balance(balance: dict):
    """Display portfolio balance."""
    available = balance.get("available_balance", balance.get("balance", 0))
    # Kalshi balance is in cents
    if isinstance(available, (int, float)) and available > 100:
        display = f"${available / 100:.2f}"
    else:
        display = f"${available:.2f}" if isinstance(available, (int, float)) else str(available)
    console.print(f"[bold]Available Balance:[/bold] [green]{display}[/green]")


def show_error(message: str):
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_info(message: str):
    console.print(f"[cyan]{message}[/cyan]")


def show_success(message: str):
    console.print(f"[bold green]{message}[/bold green]")
