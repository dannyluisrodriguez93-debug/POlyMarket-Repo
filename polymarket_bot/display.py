"""Terminal display — rich-formatted output for markets, opportunities, and trades."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .market_analyzer import Opportunity

console = Console()


def show_banner():
    console.print(
        Panel(
            "[bold cyan]Polymarket Trading Bot[/bold cyan]\n"
            "[dim]Market analysis, approval workflow, and trade execution[/dim]",
            border_style="cyan",
        )
    )


def show_markets_table(markets: list[dict], page: int = 0, page_size: int = 20):
    """Display a paginated table of markets."""
    start = page * page_size
    end = start + page_size
    page_markets = markets[start:end]

    table = Table(title=f"Markets (page {page + 1}, showing {start+1}-{min(end, len(markets))} of {len(markets)})")
    table.add_column("#", style="dim", width=5)
    table.add_column("Question", style="bold", max_width=60)
    table.add_column("Tokens", justify="center")
    table.add_column("End Date", style="dim")

    for i, market in enumerate(page_markets, start=start + 1):
        question = market.get("question", "Unknown")[:60]
        tokens = market.get("tokens", [])
        token_prices = " / ".join(
            f"{t.get('outcome', '?')}: {float(t.get('price', 0)):.2f}"
            for t in tokens[:2]
        )
        end_date = market.get("end_date_iso", "N/A")[:10]
        table.add_row(str(i), question, token_prices, end_date)

    console.print(table)
    return len(markets) > end  # has more pages


def show_opportunities(opportunities: list[Opportunity], strategy_name: str):
    """Display a table of trading opportunities."""
    if not opportunities:
        console.print(f"[dim]No {strategy_name} opportunities found.[/dim]")
        return

    style_map = {"HIGH": "bold green", "MEDIUM": "yellow", "LOW": "red"}

    table = Table(title=f"{strategy_name} Opportunities ({len(opportunities)} found)")
    table.add_column("#", style="dim", width=4)
    table.add_column("Market", max_width=45)
    table.add_column("Outcome", width=10)
    table.add_column("Price", justify="right", width=8)
    table.add_column("Spread", justify="right", width=8)
    table.add_column("Return %", justify="right", width=9)
    table.add_column("Confidence", justify="center", width=10)
    table.add_column("Side", width=5)

    for i, opp in enumerate(opportunities[:25], 1):
        conf_style = style_map.get(opp.confidence, "dim")
        table.add_row(
            str(i),
            opp.market_question[:45],
            opp.outcome[:10],
            f"{opp.current_price:.4f}",
            f"{opp.spread:.4f}",
            f"{opp.potential_return:.1f}%",
            f"[{conf_style}]{opp.confidence}[/{conf_style}]",
            opp.suggested_side,
        )

    console.print(table)


def show_opportunity_detail(opp: Opportunity):
    """Show detailed view of a single opportunity."""
    console.print(
        Panel(
            f"[bold]{opp.market_question}[/bold]\n\n"
            f"  Outcome:     {opp.outcome}\n"
            f"  Strategy:    {opp.strategy}\n"
            f"  Price:       {opp.current_price:.4f}\n"
            f"  Midpoint:    {opp.midpoint:.4f}\n"
            f"  Spread:      {opp.spread:.4f}\n"
            f"  Potential:   {opp.potential_return:.1f}%\n"
            f"  Confidence:  {opp.confidence}\n"
            f"  Side:        {opp.suggested_side}\n\n"
            f"  [dim]Reasoning: {opp.reasoning}[/dim]",
            title="Opportunity Detail",
            border_style="green" if opp.confidence == "HIGH" else "yellow",
        )
    )


def prompt_approval(opp: Opportunity, size: float, price: float, order_type: str) -> bool:
    """Prompt user to approve a trade. Returns True if approved."""
    console.print()
    console.print(
        Panel(
            f"[bold yellow]TRADE CONFIRMATION REQUIRED[/bold yellow]\n\n"
            f"  Market:     {opp.market_question}\n"
            f"  Outcome:    {opp.outcome}\n"
            f"  Side:       {opp.suggested_side}\n"
            f"  Type:       {order_type}\n"
            f"  Size:       {size:.2f} USDC\n"
            f"  Price:      {price:.4f}\n"
            f"  Est. Cost:  ${size * price:.2f}\n",
            title="Trade Approval",
            border_style="yellow",
        )
    )

    response = console.input("[bold yellow]Approve this trade? (y/N): [/bold yellow]")
    return response.strip().lower() in ("y", "yes")


def show_trade_result(result):
    """Show the result of a trade execution."""
    if result.success:
        console.print(f"[bold green]Trade executed![/bold green] {result.message}")
        if result.order_id:
            console.print(f"  Order ID: {result.order_id}")
    else:
        console.print(f"[bold red]Trade failed.[/bold red] {result.message}")


def show_orders_table(orders: list[dict]):
    """Display open orders."""
    if not orders:
        console.print("[dim]No open orders.[/dim]")
        return

    table = Table(title=f"Open Orders ({len(orders)})")
    table.add_column("#", style="dim", width=4)
    table.add_column("Order ID", width=12)
    table.add_column("Market", max_width=40)
    table.add_column("Side", width=5)
    table.add_column("Price", justify="right", width=8)
    table.add_column("Size", justify="right", width=8)
    table.add_column("Status", width=10)

    for i, order in enumerate(orders[:50], 1):
        table.add_row(
            str(i),
            str(order.get("id", ""))[:12],
            str(order.get("market", ""))[:40],
            order.get("side", ""),
            str(order.get("price", "")),
            str(order.get("original_size", order.get("size", ""))),
            order.get("status", ""),
        )

    console.print(table)


def show_error(msg: str):
    console.print(f"[bold red]Error:[/bold red] {msg}")


def show_info(msg: str):
    console.print(f"[cyan]{msg}[/cyan]")


def show_success(msg: str):
    console.print(f"[bold green]{msg}[/bold green]")
