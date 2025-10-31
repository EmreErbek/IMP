"""Portfolio management system."""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from ..core.data_fetcher import DataFetcher
from ..core.logger import IMPLogger
from ..core.exceptions import PortfolioError
from .transaction import Transaction, Position, TransactionType


class PortfolioManager:
    """Manage investment portfolio with buy/sell tracking and P&L calculation."""

    def __init__(
        self,
        data_fetcher: Optional[DataFetcher] = None,
        commission_rate: float = 0.001
    ):
        """
        Initialize PortfolioManager.

        Args:
            data_fetcher: DataFetcher instance
            commission_rate: Default commission rate (e.g., 0.001 = 0.1%)
        """
        self.data_fetcher = data_fetcher or DataFetcher()
        self.commission_rate = commission_rate
        self.transactions: List[Transaction] = []
        self.logger = IMPLogger.get_logger()

    def add_transaction(
        self,
        ticker: str,
        transaction_type: TransactionType,
        quantity: float,
        price: float,
        date: Optional[datetime] = None,
        commission: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Transaction:
        """
        Add a new transaction to the portfolio.

        Args:
            ticker: Ticker symbol
            transaction_type: Type of transaction (BUY/SELL/DIVIDEND)
            quantity: Number of shares
            price: Price per share
            date: Transaction date (defaults to now)
            commission: Commission paid (calculated if not provided)
            notes: Optional notes

        Returns:
            Created transaction

        Raises:
            PortfolioError: If transaction is invalid
        """
        if quantity <= 0:
            raise PortfolioError("Quantity must be positive")
        if price <= 0:
            raise PortfolioError("Price must be positive")

        # Calculate commission if not provided
        if commission is None:
            commission = quantity * price * self.commission_rate

        # Create transaction
        transaction = Transaction(
            ticker=ticker.upper(),
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            date=date or datetime.now(),
            commission=commission,
            notes=notes,
            transaction_id=len(self.transactions) + 1
        )

        # Validate sell transaction
        if transaction_type == TransactionType.SELL:
            current_position = self.get_position(ticker)
            if current_position is None or current_position.quantity < quantity:
                raise PortfolioError(
                    f"Cannot sell {quantity} shares of {ticker}. "
                    f"Current position: {current_position.quantity if current_position else 0}"
                )

        self.transactions.append(transaction)
        self.logger.info(f"Added {transaction_type.value} transaction: {ticker} x{quantity} @ {price}")

        return transaction

    def get_positions(self, update_prices: bool = True) -> Dict[str, Position]:
        """
        Get all current positions in the portfolio.

        Args:
            update_prices: Whether to fetch current prices

        Returns:
            Dictionary mapping tickers to positions
        """
        positions: Dict[str, Dict] = defaultdict(lambda: {"quantity": 0.0, "total_cost": 0.0})

        # Calculate positions from transactions
        for transaction in self.transactions:
            ticker = transaction.ticker
            pos = positions[ticker]

            if transaction.transaction_type == TransactionType.BUY:
                # Add to position
                pos["total_cost"] += transaction.total_cost
                pos["quantity"] += transaction.quantity

            elif transaction.transaction_type == TransactionType.SELL:
                # Reduce position using average cost
                if pos["quantity"] > 0:
                    avg_cost = pos["total_cost"] / pos["quantity"]
                    pos["total_cost"] -= avg_cost * transaction.quantity
                    pos["quantity"] -= transaction.quantity

        # Create Position objects
        result = {}
        for ticker, pos_data in positions.items():
            if pos_data["quantity"] > 0:
                avg_cost = pos_data["total_cost"] / pos_data["quantity"]
                position = Position(
                    ticker=ticker,
                    quantity=pos_data["quantity"],
                    average_cost=avg_cost
                )

                # Update current price if requested
                if update_prices:
                    try:
                        df = self.data_fetcher.get_stock_data(ticker, period="1d")
                        position.current_price = float(df["Close"].iloc[-1])
                        position.last_updated = datetime.now()
                    except Exception as e:
                        self.logger.warning(f"Failed to update price for {ticker}: {str(e)}")

                result[ticker] = position

        return result

    def get_position(self, ticker: str, update_price: bool = True) -> Optional[Position]:
        """
        Get position for a specific ticker.

        Args:
            ticker: Ticker symbol
            update_price: Whether to fetch current price

        Returns:
            Position or None if no position exists
        """
        positions = self.get_positions(update_prices=update_price)
        return positions.get(ticker.upper())

    def get_portfolio_summary(self) -> Dict[str, any]:
        """
        Get overall portfolio summary.

        Returns:
            Dictionary with portfolio statistics
        """
        positions = self.get_positions(update_prices=True)

        total_cost = sum(pos.total_cost for pos in positions.values())
        total_value = sum(pos.current_value for pos in positions.values() if pos.current_value)
        total_profit_loss = sum(pos.profit_loss for pos in positions.values() if pos.profit_loss)

        # Calculate realized P&L from sell transactions
        realized_pl = 0.0
        position_costs: Dict[str, float] = {}

        for transaction in self.transactions:
            ticker = transaction.ticker

            if transaction.transaction_type == TransactionType.BUY:
                if ticker not in position_costs:
                    position_costs[ticker] = {"quantity": 0.0, "total_cost": 0.0}
                position_costs[ticker]["quantity"] += transaction.quantity
                position_costs[ticker]["total_cost"] += transaction.total_cost

            elif transaction.transaction_type == TransactionType.SELL:
                if ticker in position_costs and position_costs[ticker]["quantity"] > 0:
                    avg_cost = position_costs[ticker]["total_cost"] / position_costs[ticker]["quantity"]
                    cost_of_sold = avg_cost * transaction.quantity
                    proceeds = (transaction.quantity * transaction.price) - transaction.commission
                    realized_pl += proceeds - cost_of_sold

                    # Update remaining position
                    position_costs[ticker]["quantity"] -= transaction.quantity
                    position_costs[ticker]["total_cost"] -= cost_of_sold

        return {
            "total_positions": len(positions),
            "total_invested": total_cost,
            "current_value": total_value,
            "unrealized_profit_loss": total_profit_loss,
            "realized_profit_loss": realized_pl,
            "total_profit_loss": total_profit_loss + realized_pl,
            "return_percentage": (total_profit_loss / total_cost * 100) if total_cost > 0 else 0,
            "positions": {ticker: pos.to_dict() for ticker, pos in positions.items()}
        }

    def get_transaction_history(
        self,
        ticker: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get transaction history as DataFrame.

        Args:
            ticker: Filter by ticker (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)

        Returns:
            DataFrame with transaction history
        """
        filtered_transactions = self.transactions

        # Apply filters
        if ticker:
            filtered_transactions = [t for t in filtered_transactions if t.ticker == ticker.upper()]
        if start_date:
            filtered_transactions = [t for t in filtered_transactions if t.date >= start_date]
        if end_date:
            filtered_transactions = [t for t in filtered_transactions if t.date <= end_date]

        # Convert to DataFrame
        if not filtered_transactions:
            return pd.DataFrame()

        data = [t.to_dict() for t in filtered_transactions]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        return df.sort_values("date", ascending=False)

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Calculate portfolio performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        summary = self.get_portfolio_summary()

        metrics = {
            "total_return": summary["total_profit_loss"],
            "total_return_pct": summary["return_percentage"],
            "unrealized_return": summary["unrealized_profit_loss"],
            "realized_return": summary["realized_profit_loss"],
        }

        # Calculate best and worst positions
        positions = summary["positions"]
        if positions:
            best_position = max(
                positions.items(),
                key=lambda x: x[1].get("profit_loss_pct", float("-inf"))
            )
            worst_position = min(
                positions.items(),
                key=lambda x: x[1].get("profit_loss_pct", float("inf"))
            )

            metrics["best_performer"] = {
                "ticker": best_position[0],
                "return_pct": best_position[1].get("profit_loss_pct")
            }
            metrics["worst_performer"] = {
                "ticker": worst_position[0],
                "return_pct": worst_position[1].get("profit_loss_pct")
            }

        return metrics

    def export_to_excel(self, filepath: str):
        """
        Export portfolio data to Excel.

        Args:
            filepath: Path to save Excel file
        """
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # Portfolio summary
            summary = self.get_portfolio_summary()
            summary_df = pd.DataFrame([{
                "Total Positions": summary["total_positions"],
                "Total Invested": summary["total_invested"],
                "Current Value": summary["current_value"],
                "Unrealized P&L": summary["unrealized_profit_loss"],
                "Realized P&L": summary["realized_profit_loss"],
                "Total P&L": summary["total_profit_loss"],
                "Return %": summary["return_percentage"]
            }])
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Positions
            if summary["positions"]:
                positions_df = pd.DataFrame([
                    pos for pos in summary["positions"].values()
                ])
                positions_df.to_excel(writer, sheet_name="Positions", index=False)

            # Transaction history
            transactions_df = self.get_transaction_history()
            if not transactions_df.empty:
                transactions_df.to_excel(writer, sheet_name="Transactions", index=False)

        self.logger.info(f"Portfolio exported to {filepath}")
