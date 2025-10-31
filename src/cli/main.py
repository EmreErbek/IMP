"""Command-line interface for IMP application."""

import click
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from datetime import datetime

from ..core.data_fetcher import DataFetcher
from ..core.logger import IMPLogger
from ..core.exceptions import IMPException
from ..analysis.stock_analyzer import StockAnalyzer
from ..portfolio.portfolio_manager import PortfolioManager
from ..portfolio.transaction import TransactionType
from ..database.db_manager import DatabaseManager

console = Console()


def load_config():
    """Load configuration from config file."""
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


def init_components(config):
    """Initialize application components."""
    # Setup logger
    log_config = config.get("logging", {})
    logger = IMPLogger.get_logger(
        level=log_config.get("level", "INFO"),
        log_file=log_config.get("file_path", "data/imp.log"),
        max_bytes=log_config.get("max_bytes", 10485760),
        backup_count=log_config.get("backup_count", 5)
    )

    # Initialize components
    data_config = config.get("data", {})
    data_fetcher = DataFetcher(
        market_suffix=data_config.get("market_suffix", ".IS"),
        cache_enabled=data_config.get("cache_enabled", True)
    )

    analyzer = StockAnalyzer(data_fetcher)

    portfolio_config = config.get("portfolio", {})
    portfolio = PortfolioManager(
        data_fetcher=data_fetcher,
        commission_rate=portfolio_config.get("commission_rate", 0.001)
    )

    db_config = config.get("database", {})
    db = DatabaseManager(
        db_path=db_config.get("path", "data/imp.db"),
        echo=db_config.get("echo", False)
    )

    return logger, data_fetcher, analyzer, portfolio, db


# Load config and initialize
config = load_config()


@click.group()
def cli():
    """Investment Management Panel - Stock Analysis & Portfolio Management Tool"""
    pass


@cli.command()
@click.argument("ticker")
@click.option("--period", "-p", default="1y", help="Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)")
@click.option("--save", "-s", is_flag=True, help="Save analysis to database")
def analyze(ticker, period, save):
    """Analyze a stock with technical indicators."""
    try:
        logger, data_fetcher, analyzer, portfolio, db = init_components(config)

        console.print(f"\n[bold cyan]Analyzing {ticker.upper()}...[/bold cyan]\n")

        # Perform analysis
        analysis = analyzer.analyze_stock(ticker, period=period)

        # Display results
        display_analysis(analysis)

        # Save to database if requested
        if save:
            db.save_analysis(ticker, analysis)
            console.print(f"\n[green]✓ Analysis saved to database[/green]")

    except IMPException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")


@cli.command()
@click.argument("tickers", nargs=-1, required=True)
@click.option("--period", "-p", default="1y", help="Data period")
def compare(tickers, period):
    """Compare multiple stocks."""
    try:
        logger, data_fetcher, analyzer, portfolio, db = init_components(config)

        console.print(f"\n[bold cyan]Comparing {len(tickers)} stocks...[/bold cyan]\n")

        # Compare stocks
        comparison = analyzer.compare_stocks(list(tickers), period=period)

        # Display comparison table
        table = Table(title="Stock Comparison", box=box.ROUNDED)

        for column in comparison.columns:
            table.add_column(column, style="cyan")

        for _, row in comparison.iterrows():
            table.add_row(*[str(val) for val in row])

        console.print(table)

    except IMPException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")


@cli.group()
def portfolio():
    """Portfolio management commands."""
    pass


@portfolio.command()
@click.argument("ticker")
@click.argument("quantity", type=float)
@click.argument("price", type=float)
@click.option("--commission", "-c", type=float, help="Commission amount")
@click.option("--date", "-d", help="Transaction date (YYYY-MM-DD)")
@click.option("--notes", "-n", help="Transaction notes")
def buy(ticker, quantity, price, commission, date, notes):
    """Buy stocks and add to portfolio."""
    try:
        logger, data_fetcher, analyzer, pm, db = init_components(config)

        # Parse date if provided
        transaction_date = datetime.strptime(date, "%Y-%m-%d") if date else None

        # Add transaction
        transaction = pm.add_transaction(
            ticker=ticker,
            transaction_type=TransactionType.BUY,
            quantity=quantity,
            price=price,
            date=transaction_date,
            commission=commission,
            notes=notes
        )

        # Save to database
        db.add_transaction(
            ticker=ticker,
            transaction_type="BUY",
            quantity=quantity,
            price=price,
            commission=commission or 0.0,
            date=transaction_date,
            notes=notes
        )

        console.print(f"\n[green]✓ Bought {quantity} shares of {ticker} at {price} TRY[/green]")
        console.print(f"Total cost: {transaction.total_cost:.2f} TRY\n")

    except IMPException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")


@portfolio.command()
@click.argument("ticker")
@click.argument("quantity", type=float)
@click.argument("price", type=float)
@click.option("--commission", "-c", type=float, help="Commission amount")
@click.option("--date", "-d", help="Transaction date (YYYY-MM-DD)")
@click.option("--notes", "-n", help="Transaction notes")
def sell(ticker, quantity, price, commission, date, notes):
    """Sell stocks from portfolio."""
    try:
        logger, data_fetcher, analyzer, pm, db = init_components(config)

        # Parse date if provided
        transaction_date = datetime.strptime(date, "%Y-%m-%d") if date else None

        # Add transaction
        transaction = pm.add_transaction(
            ticker=ticker,
            transaction_type=TransactionType.SELL,
            quantity=quantity,
            price=price,
            date=transaction_date,
            commission=commission,
            notes=notes
        )

        # Save to database
        db.add_transaction(
            ticker=ticker,
            transaction_type="SELL",
            quantity=quantity,
            price=price,
            commission=commission or 0.0,
            date=transaction_date,
            notes=notes
        )

        console.print(f"\n[green]✓ Sold {quantity} shares of {ticker} at {price} TRY[/green]")
        console.print(f"Net proceeds: {transaction.net_amount:.2f} TRY\n")

    except IMPException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")


@portfolio.command()
def summary():
    """Show portfolio summary."""
    try:
        logger, data_fetcher, analyzer, pm, db = init_components(config)

        # Load transactions from database
        db_transactions = db.get_transactions()
        for t in db_transactions:
            try:
                pm.add_transaction(
                    ticker=t["ticker"],
                    transaction_type=TransactionType[t["type"]],
                    quantity=t["quantity"],
                    price=t["price"],
                    date=t["date"],
                    commission=t["commission"],
                    notes=t["notes"]
                )
            except:
                pass  # Skip duplicates

        console.print("\n[bold cyan]Portfolio Summary[/bold cyan]\n")

        summary = pm.get_portfolio_summary()

        # Summary table
        summary_table = Table(box=box.ROUNDED, show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")

        summary_table.add_row("Total Positions", str(summary["total_positions"]))
        summary_table.add_row("Total Invested", f"{summary['total_invested']:.2f} TRY")
        summary_table.add_row("Current Value", f"{summary['current_value']:.2f} TRY")
        summary_table.add_row("Unrealized P&L",
                             f"[{'green' if summary['unrealized_profit_loss'] >= 0 else 'red'}]{summary['unrealized_profit_loss']:.2f} TRY[/]")
        summary_table.add_row("Realized P&L",
                             f"[{'green' if summary['realized_profit_loss'] >= 0 else 'red'}]{summary['realized_profit_loss']:.2f} TRY[/]")
        summary_table.add_row("Total P&L",
                             f"[{'green' if summary['total_profit_loss'] >= 0 else 'red'}]{summary['total_profit_loss']:.2f} TRY[/]")
        summary_table.add_row("Return",
                             f"[{'green' if summary['return_percentage'] >= 0 else 'red'}]{summary['return_percentage']:.2f}%[/]")

        console.print(summary_table)

        # Positions table
        if summary["positions"]:
            console.print("\n[bold cyan]Positions[/bold cyan]\n")
            positions_table = Table(box=box.ROUNDED)
            positions_table.add_column("Ticker", style="cyan")
            positions_table.add_column("Quantity", justify="right")
            positions_table.add_column("Avg Cost", justify="right")
            positions_table.add_column("Current", justify="right")
            positions_table.add_column("P&L", justify="right")
            positions_table.add_column("P&L %", justify="right")

            for ticker, pos in summary["positions"].items():
                pl_pct = pos.get("profit_loss_pct", 0) or 0
                pl = pos.get("profit_loss", 0) or 0
                color = "green" if pl >= 0 else "red"

                positions_table.add_row(
                    ticker,
                    f"{pos['quantity']:.2f}",
                    f"{pos['average_cost']:.2f}",
                    f"{pos.get('current_price', 0):.2f}",
                    f"[{color}]{pl:.2f}[/]",
                    f"[{color}]{pl_pct:.2f}%[/]"
                )

            console.print(positions_table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


@cli.group()
def watchlist():
    """Watchlist management commands."""
    pass


@watchlist.command()
@click.argument("ticker")
@click.option("--name", "-n", help="Company name")
@click.option("--target", "-t", type=float, help="Target price")
@click.option("--stop", "-s", type=float, help="Stop loss price")
@click.option("--notes", help="Notes")
def add(ticker, name, target, stop, notes):
    """Add a ticker to watchlist."""
    try:
        logger, data_fetcher, analyzer, portfolio, db = init_components(config)

        db.add_to_watchlist(
            ticker=ticker,
            name=name,
            target_price=target,
            stop_loss=stop,
            notes=notes
        )

        console.print(f"\n[green]✓ Added {ticker.upper()} to watchlist[/green]\n")

    except IMPException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")


@watchlist.command()
def show():
    """Show watchlist."""
    try:
        logger, data_fetcher, analyzer, portfolio, db = init_components(config)

        items = db.get_watchlist()

        if not items:
            console.print("\n[yellow]Watchlist is empty[/yellow]\n")
            return

        console.print("\n[bold cyan]Watchlist[/bold cyan]\n")

        table = Table(box=box.ROUNDED)
        table.add_column("Ticker", style="cyan")
        table.add_column("Name")
        table.add_column("Target", justify="right")
        table.add_column("Stop Loss", justify="right")
        table.add_column("Added", justify="right")

        for item in items:
            table.add_row(
                item["ticker"],
                item["name"] or "-",
                f"{item['target_price']:.2f}" if item["target_price"] else "-",
                f"{item['stop_loss']:.2f}" if item["stop_loss"] else "-",
                item["added_date"].strftime("%Y-%m-%d")
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


@watchlist.command()
@click.argument("ticker")
def remove(ticker):
    """Remove a ticker from watchlist."""
    try:
        logger, data_fetcher, analyzer, portfolio, db = init_components(config)

        if db.remove_from_watchlist(ticker):
            console.print(f"\n[green]✓ Removed {ticker.upper()} from watchlist[/green]\n")
        else:
            console.print(f"\n[yellow]! {ticker.upper()} not found in watchlist[/yellow]\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


def display_analysis(analysis):
    """Display analysis results in a formatted way."""
    latest = analysis["latest_data"]
    signals = analysis["technical_signals"]
    trend = analysis["trend_analysis"]
    volatility = analysis["volatility"]
    summary = analysis["summary"]

    # Price info
    price_panel = Panel(
        f"[bold white]Close:[/] {latest['close']:.2f} TRY\n"
        f"[bold white]Change:[/] {latest.get('price_change', 0):.2f} ({latest.get('price_change_pct', 0):.2f}%)\n"
        f"[bold white]High:[/] {latest['high']:.2f} | [bold white]Low:[/] {latest['low']:.2f}",
        title="[bold cyan]Price Information[/]",
        box=box.ROUNDED
    )
    console.print(price_panel)

    # Technical indicators
    indicators_table = Table(title="Technical Indicators", box=box.ROUNDED)
    indicators_table.add_column("Indicator", style="cyan")
    indicators_table.add_column("Value", justify="right")
    indicators_table.add_column("Signal", justify="center")

    if "rsi" in latest:
        signal_color = "red" if signals.get("rsi") == "OVERBOUGHT" else "green" if signals.get("rsi") == "OVERSOLD" else "yellow"
        indicators_table.add_row("RSI", f"{latest['rsi']:.2f}", f"[{signal_color}]{signals.get('rsi', '-')}[/]")

    if "macd" in latest:
        signal_color = "green" if "BULLISH" in signals.get("macd", "") else "red" if "BEARISH" in signals.get("macd", "") else "yellow"
        indicators_table.add_row("MACD", f"{latest['macd']:.4f}", f"[{signal_color}]{signals.get('macd', '-')}[/]")

    if "bb_upper" in latest:
        signal_color = "yellow"
        indicators_table.add_row("Bollinger Bands",
                                f"{latest['bb_lower']:.2f} - {latest['bb_upper']:.2f}",
                                f"[{signal_color}]{signals.get('bollinger', '-')}[/]")

    console.print("\n")
    console.print(indicators_table)

    # Summary
    overall_color = "green" if summary["overall_signal"] == "BULLISH" else "red" if summary["overall_signal"] == "BEARISH" else "yellow"
    summary_panel = Panel(
        f"[bold]Overall Signal:[/] [{overall_color}]{summary['overall_signal']}[/]\n"
        f"[bold]Confidence:[/] {summary['confidence'] * 100:.1f}%\n"
        f"[bold]Bullish Indicators:[/] {summary['bullish_indicators']}\n"
        f"[bold]Bearish Indicators:[/] {summary['bearish_indicators']}",
        title="[bold cyan]Analysis Summary[/]",
        box=box.ROUNDED
    )
    console.print("\n")
    console.print(summary_panel)
    console.print()


if __name__ == "__main__":
    cli()
