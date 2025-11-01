"""Database models for alert system."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum
from datetime import datetime
import enum

from .models import Base


class AlertTypeEnum(enum.Enum):
    """Alert types."""
    PRICE_TARGET = "PRICE_TARGET"
    STOP_LOSS = "STOP_LOSS"
    RSI_OVERBOUGHT = "RSI_OVERBOUGHT"
    RSI_OVERSOLD = "RSI_OVERSOLD"
    MACD_CROSSOVER = "MACD_CROSSOVER"
    CUSTOM = "CUSTOM"


class AlertStatusEnum(enum.Enum):
    """Alert statuses."""
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    DISABLED = "DISABLED"


class AlertModel(Base):
    """Database model for alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    alert_type = Column(Enum(AlertTypeEnum), nullable=False)
    status = Column(Enum(AlertStatusEnum), default=AlertStatusEnum.ACTIVE, nullable=False)

    # Price-based alerts
    target_price = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)

    # Technical indicator alerts
    indicator_name = Column(String(50), nullable=True)
    indicator_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)

    # Notification settings
    email_notification = Column(Boolean, default=True)
    notification_email = Column(String(200), nullable=True)

    # Alert metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    triggered_at = Column(DateTime, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Alert(id={self.id}, ticker={self.ticker}, type={self.alert_type}, status={self.status})>"


class AlertHistoryModel(Base):
    """Database model for alert history."""

    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    triggered_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    trigger_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    indicator_value = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    notification_sent = Column(Boolean, default=False)

    def __repr__(self):
        return f"<AlertHistory(id={self.id}, alert_id={self.alert_id}, ticker={self.ticker})>"
