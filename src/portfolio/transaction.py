"""Transaction models for portfolio management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TransactionType(Enum):
    """Types of transactions."""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"


@dataclass
class Transaction:
    """Represents a single transaction."""

    ticker: str
    transaction_type: TransactionType
    quantity: float
    price: float
    date: datetime = field(default_factory=datetime.now)
    commission: float = 0.0
    notes: Optional[str] = None
    transaction_id: Optional[int] = None

    @property
    def total_cost(self) -> float:
        """Calculate total cost including commission."""
        return (self.quantity * self.price) + self.commission

    @property
    def net_amount(self) -> float:
        """
        Calculate net amount (positive for sell, negative for buy).

        Returns:
            Net amount of the transaction
        """
        if self.transaction_type == TransactionType.SELL:
            return (self.quantity * self.price) - self.commission
        elif self.transaction_type == TransactionType.BUY:
            return -((self.quantity * self.price) + self.commission)
        else:  # DIVIDEND
            return self.quantity * self.price

    def to_dict(self) -> dict:
        """Convert transaction to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "ticker": self.ticker,
            "type": self.transaction_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "date": self.date.isoformat(),
            "commission": self.commission,
            "total_cost": self.total_cost,
            "net_amount": self.net_amount,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Create transaction from dictionary."""
        return cls(
            transaction_id=data.get("transaction_id"),
            ticker=data["ticker"],
            transaction_type=TransactionType(data["type"]),
            quantity=data["quantity"],
            price=data["price"],
            date=datetime.fromisoformat(data["date"]),
            commission=data.get("commission", 0.0),
            notes=data.get("notes")
        )


@dataclass
class Position:
    """Represents a stock position in the portfolio."""

    ticker: str
    quantity: float
    average_cost: float
    current_price: Optional[float] = None
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def total_cost(self) -> float:
        """Total cost of the position."""
        return self.quantity * self.average_cost

    @property
    def current_value(self) -> Optional[float]:
        """Current market value of the position."""
        if self.current_price is not None:
            return self.quantity * self.current_price
        return None

    @property
    def profit_loss(self) -> Optional[float]:
        """Profit or loss on the position."""
        if self.current_value is not None:
            return self.current_value - self.total_cost
        return None

    @property
    def profit_loss_percentage(self) -> Optional[float]:
        """Profit or loss percentage."""
        if self.profit_loss is not None and self.total_cost > 0:
            return (self.profit_loss / self.total_cost) * 100
        return None

    def to_dict(self) -> dict:
        """Convert position to dictionary."""
        return {
            "ticker": self.ticker,
            "quantity": self.quantity,
            "average_cost": self.average_cost,
            "total_cost": self.total_cost,
            "current_price": self.current_price,
            "current_value": self.current_value,
            "profit_loss": self.profit_loss,
            "profit_loss_pct": self.profit_loss_percentage,
            "last_updated": self.last_updated.isoformat()
        }
