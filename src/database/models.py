"""Database models for IMP application."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class TransactionTypeEnum(enum.Enum):
    """Transaction types for database."""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"


class TransactionModel(Base):
    """Database model for transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Transaction(id={self.id}, ticker={self.ticker}, type={self.transaction_type}, qty={self.quantity})>"


class WatchlistModel(Base):
    """Database model for watchlist."""

    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=True)
    added_date = Column(DateTime, default=datetime.now)
    notes = Column(Text, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Watchlist(id={self.id}, ticker={self.ticker})>"


class AnalysisHistoryModel(Base):
    """Database model for storing analysis history."""

    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    analysis_date = Column(DateTime, default=datetime.now, index=True)
    close_price = Column(Float, nullable=False)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    overall_signal = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AnalysisHistory(id={self.id}, ticker={self.ticker}, date={self.analysis_date})>"
