"""Database manager for IMP application."""

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .models import Base, TransactionModel, WatchlistModel, AnalysisHistoryModel, TransactionTypeEnum
from ..core.logger import IMPLogger
from ..core.exceptions import DatabaseError


class DatabaseManager:
    """Manage database operations for IMP."""

    def __init__(self, db_path: str = "data/imp.db", echo: bool = False):
        """
        Initialize DatabaseManager.

        Args:
            db_path: Path to SQLite database file
            echo: Whether to echo SQL statements (for debugging)
        """
        self.logger = IMPLogger.get_logger()

        # Create data directory if it doesn't exist
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Create engine and session
        self.engine = create_engine(f"sqlite:///{db_path}", echo=echo)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables
        self._create_tables()

    def _create_tables(self):
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {str(e)}")
            raise DatabaseError(f"Failed to create database tables: {str(e)}")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    # Transaction operations
    def add_transaction(
        self,
        ticker: str,
        transaction_type: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        date: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Add a new transaction to the database.

        Args:
            ticker: Ticker symbol
            transaction_type: Type of transaction (BUY/SELL/DIVIDEND)
            quantity: Number of shares
            price: Price per share
            commission: Commission paid
            date: Transaction date
            notes: Optional notes

        Returns:
            ID of created transaction
        """
        session = self.get_session()
        try:
            transaction = TransactionModel(
                ticker=ticker.upper(),
                transaction_type=TransactionTypeEnum[transaction_type],
                quantity=quantity,
                price=price,
                commission=commission,
                date=date or datetime.now(),
                notes=notes
            )
            session.add(transaction)
            session.commit()
            transaction_id = transaction.id
            self.logger.info(f"Added transaction {transaction_id} to database")
            return transaction_id
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to add transaction: {str(e)}")
            raise DatabaseError(f"Failed to add transaction: {str(e)}")
        finally:
            session.close()

    def get_transactions(
        self,
        ticker: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions from database.

        Args:
            ticker: Filter by ticker (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Maximum number of results (optional)

        Returns:
            List of transactions as dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(TransactionModel)

            if ticker:
                query = query.filter(TransactionModel.ticker == ticker.upper())
            if start_date:
                query = query.filter(TransactionModel.date >= start_date)
            if end_date:
                query = query.filter(TransactionModel.date <= end_date)

            query = query.order_by(desc(TransactionModel.date))

            if limit:
                query = query.limit(limit)

            transactions = query.all()

            return [
                {
                    "id": t.id,
                    "ticker": t.ticker,
                    "type": t.transaction_type.value,
                    "quantity": t.quantity,
                    "price": t.price,
                    "commission": t.commission,
                    "date": t.date,
                    "notes": t.notes
                }
                for t in transactions
            ]
        finally:
            session.close()

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction from the database.

        Args:
            transaction_id: ID of transaction to delete

        Returns:
            True if successful
        """
        session = self.get_session()
        try:
            transaction = session.query(TransactionModel).filter(
                TransactionModel.id == transaction_id
            ).first()

            if transaction:
                session.delete(transaction)
                session.commit()
                self.logger.info(f"Deleted transaction {transaction_id}")
                return True
            else:
                self.logger.warning(f"Transaction {transaction_id} not found")
                return False
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to delete transaction: {str(e)}")
            raise DatabaseError(f"Failed to delete transaction: {str(e)}")
        finally:
            session.close()

    # Watchlist operations
    def add_to_watchlist(
        self,
        ticker: str,
        name: Optional[str] = None,
        notes: Optional[str] = None,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> int:
        """
        Add a ticker to the watchlist.

        Args:
            ticker: Ticker symbol
            name: Company name
            notes: Optional notes
            target_price: Target price for alerts
            stop_loss: Stop loss price for alerts

        Returns:
            ID of watchlist entry
        """
        session = self.get_session()
        try:
            # Check if already exists
            existing = session.query(WatchlistModel).filter(
                WatchlistModel.ticker == ticker.upper()
            ).first()

            if existing:
                raise DatabaseError(f"{ticker} is already in watchlist")

            watchlist_item = WatchlistModel(
                ticker=ticker.upper(),
                name=name,
                notes=notes,
                target_price=target_price,
                stop_loss=stop_loss
            )
            session.add(watchlist_item)
            session.commit()
            item_id = watchlist_item.id
            self.logger.info(f"Added {ticker} to watchlist")
            return item_id
        except DatabaseError:
            raise
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to add to watchlist: {str(e)}")
            raise DatabaseError(f"Failed to add to watchlist: {str(e)}")
        finally:
            session.close()

    def get_watchlist(self) -> List[Dict[str, Any]]:
        """
        Get all items in the watchlist.

        Returns:
            List of watchlist items as dictionaries
        """
        session = self.get_session()
        try:
            items = session.query(WatchlistModel).order_by(WatchlistModel.added_date.desc()).all()
            return [
                {
                    "id": item.id,
                    "ticker": item.ticker,
                    "name": item.name,
                    "added_date": item.added_date,
                    "notes": item.notes,
                    "target_price": item.target_price,
                    "stop_loss": item.stop_loss
                }
                for item in items
            ]
        finally:
            session.close()

    def remove_from_watchlist(self, ticker: str) -> bool:
        """
        Remove a ticker from the watchlist.

        Args:
            ticker: Ticker symbol

        Returns:
            True if successful
        """
        session = self.get_session()
        try:
            item = session.query(WatchlistModel).filter(
                WatchlistModel.ticker == ticker.upper()
            ).first()

            if item:
                session.delete(item)
                session.commit()
                self.logger.info(f"Removed {ticker} from watchlist")
                return True
            else:
                self.logger.warning(f"{ticker} not found in watchlist")
                return False
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to remove from watchlist: {str(e)}")
            raise DatabaseError(f"Failed to remove from watchlist: {str(e)}")
        finally:
            session.close()

    # Analysis history operations
    def save_analysis(
        self,
        ticker: str,
        analysis_data: Dict[str, Any]
    ) -> int:
        """
        Save analysis results to history.

        Args:
            ticker: Ticker symbol
            analysis_data: Analysis results dictionary

        Returns:
            ID of analysis record
        """
        session = self.get_session()
        try:
            latest = analysis_data.get("latest_data", {})
            summary = analysis_data.get("summary", {})

            analysis = AnalysisHistoryModel(
                ticker=ticker.upper(),
                close_price=latest.get("close"),
                rsi=latest.get("rsi"),
                macd=latest.get("macd"),
                macd_signal=latest.get("macd_signal"),
                bb_upper=latest.get("bb_upper"),
                bb_middle=latest.get("bb_middle"),
                bb_lower=latest.get("bb_lower"),
                overall_signal=summary.get("overall_signal")
            )
            session.add(analysis)
            session.commit()
            analysis_id = analysis.id
            self.logger.info(f"Saved analysis for {ticker}")
            return analysis_id
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to save analysis: {str(e)}")
            raise DatabaseError(f"Failed to save analysis: {str(e)}")
        finally:
            session.close()

    def get_analysis_history(
        self,
        ticker: str,
        limit: Optional[int] = 30
    ) -> List[Dict[str, Any]]:
        """
        Get analysis history for a ticker.

        Args:
            ticker: Ticker symbol
            limit: Maximum number of results

        Returns:
            List of analysis records
        """
        session = self.get_session()
        try:
            query = session.query(AnalysisHistoryModel).filter(
                AnalysisHistoryModel.ticker == ticker.upper()
            ).order_by(desc(AnalysisHistoryModel.analysis_date))

            if limit:
                query = query.limit(limit)

            analyses = query.all()

            return [
                {
                    "id": a.id,
                    "ticker": a.ticker,
                    "date": a.analysis_date,
                    "close_price": a.close_price,
                    "rsi": a.rsi,
                    "macd": a.macd,
                    "overall_signal": a.overall_signal
                }
                for a in analyses
            ]
        finally:
            session.close()
