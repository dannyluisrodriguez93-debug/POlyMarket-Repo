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
    banner.append("High-Probability Market Scanner", style="dim")
    banner.append("\n")
    banner.append("Scanning for 80%+ probability wagers", style="dim italic")
    console.print(Panel(banner, border_style="cyan", padding=(1, 2)))


def show_markets_table(markets: list[dict], page: int = 1, page_size: int = 20):
    """Display markets in a paginated table."""
    start = (page - 1) * page_size
    end = start + page_size
    page_markets = markets[start:end]
    total_pages = (len(markets) + page_size - 1) // page_size

    table = Table(
        title=f"Kalshi Markets (Page {page}/{total_pages} — {len(markets)} total)",
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
        yes_price = m.get("yes_price", "—")
        no_price = m.get("no_price", "—")
        if isinstance(yes_price, (int, float)):
            yes_display = f"{yes_price}c"
        else:
            yes_display = str(yes_price)
        if isinstance(no_price, (int, float)):
            no_display = f"{no_price}c"
        else:
            no_display = str(no_price)

        close_time = m.get("close_time", m.get("expiration_time", "—"))
        if isinstance(close_time, str) and len(close_time) > 16:
            close_time = close_time[:16]

        table.add_row(
            str(i),
            m.get("ticker", "—"),
            m.get("title", "—"),
            yes_display,
            no_display,
            close_time,
            m.get("status", "—"),
        )

    console.print(table)


def show_opportunities(opportunities: list[Opportunity]):
    """Display high-probability opportunities in a table."""
    if not opportunities:
        console.print("[yellow]No opportunities found at the current probability threshold.[/yellow]")
        return

    table = Table(
        title=f"High-Probability Opportunities ({len(opportunities)} found)",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=5)
    table.add_column("Market", style="white", max_width=45)
    table.add_column("Side", style="bold", width=5)
    table.add_column("Prob", justify="right", style="cyan", width=7)
    table.add_column("Price", justify="right", style="green", width=7)
    table.add_column("Return", justify="right", style="yellow", width=8)
    table.add_column("Close Date", style="dim", max_width=16)

    for i, opp in enumerate(opportunities, 1):
        side_style = "green" if opp.outcome == "yes" else "red"
        close_display = opp.close_time[:16] if len(opp.close_time) > 16 else opp.close_time

        table.add_row(
            str(i),
            opp.market_title[:45],
            Text(opp.outcome.upper(), style=side_style),
            f"{opp.probability:.0%}",
            f"{opp.price_cents}c",
            f"{opp.expected_return:.1f}%",
            close_display,
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
    detail.append(f"\nClose Time: ", style="dim")
    detail.append(opp.close_time, style="white")
    detail.append(f"\n\nReasoning: ", style="dim")
    detail.append(opp.reasoning, style="italic")

    console.print(Panel(detail, title="Opportunity Detail", border_style="cyan", padding=(1, 2)))


def prompt_approval(opp: Opportunity, count: int) -> bool:
    """Ask user to confirm a trade."""
    cost_dollars = count * opp.price_cents / 100
    potential_profit = count * (100 - opp.price_cents) / 100

    console.print(f"\n[bold]Trade Confirmation:[/bold]")
    console.print(f"  Market: {opp.market_title}")
    console.print(f"  Side:   {opp.outcome.upper()} at {opp.price_cents}c")
    console.print(f"  Count:  {count} contracts")
    console.print(f"  Cost:   ${cost_dollars:.2f}")
    console.print(f"  Profit: ${potential_profit:.2f} if correct ({opp.expected_return:.1f}% return)")
    console.print()

    answer = console.input("[bold yellow]Confirm trade? (yes/no): [/bold yellow]").strip().lower()
    return answer in ("yes", "y")


def show_trade_result(result: dict):
    """Display trade execution result."""
    if result.get("success"):
        console.print(Panel(
            f"[bold green]Order placed successfully![/bold green]\n"
            f"Order ID: {result.get('order_id', '—')}\n"
            f"Status: {result.get('status', '—')}",
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
        side = order.get("side", "—")
        side_style = "green" if side == "yes" else "red"
        table.add_row(
            str(i),
            order.get("order_id", "—")[:20],
            order.get("ticker", "—"),
            Text(side.upper(), style=side_style),
            f"{order.get('yes_price', order.get('no_price', '—'))}c",
            str(order.get("count", "—")),
            str(order.get("remaining_count", "—")),
            order.get("status", "—"),
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
