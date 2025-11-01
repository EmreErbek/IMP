"""Alert management system."""

import schedule
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from threading import Thread

from ..core.data_fetcher import DataFetcher
from ..core.logger import IMPLogger
from ..analysis.stock_analyzer import StockAnalyzer
from .email_service import EmailService


class AlertManager:
    """Manage price and technical indicator alerts."""

    def __init__(
        self,
        data_fetcher: Optional[DataFetcher] = None,
        email_service: Optional[EmailService] = None,
        check_interval_minutes: int = 15
    ):
        """
        Initialize AlertManager.

        Args:
            data_fetcher: DataFetcher instance
            email_service: EmailService instance
            check_interval_minutes: How often to check alerts (in minutes)
        """
        self.data_fetcher = data_fetcher or DataFetcher()
        self.analyzer = StockAnalyzer(self.data_fetcher)
        self.email_service = email_service or EmailService()
        self.check_interval = check_interval_minutes
        self.logger = IMPLogger.get_logger()
        self._running = False
        self._thread: Optional[Thread] = None

    def check_price_alert(
        self,
        ticker: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        notification_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if price alert should trigger.

        Args:
            ticker: Ticker symbol
            target_price: Target price for upside alert
            stop_loss: Stop loss price for downside alert
            notification_email: Email to send notification to

        Returns:
            Dictionary with alert status and details
        """
        result = {
            "ticker": ticker,
            "triggered": False,
            "alert_type": None,
            "current_price": None,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "timestamp": datetime.now()
        }

        try:
            # Get current price
            df = self.data_fetcher.get_stock_data(ticker, period="1d")
            current_price = float(df["Close"].iloc[-1])
            result["current_price"] = current_price

            # Check target price
            if target_price and current_price >= target_price:
                result["triggered"] = True
                result["alert_type"] = "TARGET_HIT"
                self.logger.info(f"Price target hit for {ticker}: {current_price:.2f} >= {target_price:.2f}")

                # Send notification
                if notification_email and self.email_service.enabled:
                    self.email_service.send_price_alert(
                        to_email=notification_email,
                        ticker=ticker,
                        current_price=current_price,
                        target_price=target_price,
                        alert_type="TARGET_HIT"
                    )

            # Check stop loss
            elif stop_loss and current_price <= stop_loss:
                result["triggered"] = True
                result["alert_type"] = "STOP_LOSS_HIT"
                self.logger.warning(f"Stop loss hit for {ticker}: {current_price:.2f} <= {stop_loss:.2f}")

                # Send notification
                if notification_email and self.email_service.enabled:
                    self.email_service.send_price_alert(
                        to_email=notification_email,
                        ticker=ticker,
                        current_price=current_price,
                        target_price=stop_loss,
                        alert_type="STOP_LOSS_HIT"
                    )

        except Exception as e:
            self.logger.error(f"Error checking price alert for {ticker}: {str(e)}")
            result["error"] = str(e)

        return result

    def check_technical_alert(
        self,
        ticker: str,
        indicator: str,
        condition: str,
        threshold: float,
        notification_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if technical indicator alert should trigger.

        Args:
            ticker: Ticker symbol
            indicator: Indicator name (RSI, MACD, etc.)
            condition: Condition (above, below, crosses_above, crosses_below)
            threshold: Threshold value
            notification_email: Email to send notification to

        Returns:
            Dictionary with alert status and details
        """
        result = {
            "ticker": ticker,
            "triggered": False,
            "indicator": indicator,
            "condition": condition,
            "threshold": threshold,
            "current_value": None,
            "timestamp": datetime.now()
        }

        try:
            # Analyze stock
            analysis = self.analyzer.analyze_stock(ticker, period="1mo")
            latest = analysis.get("latest_data", {})

            # Get indicator value
            indicator_map = {
                "RSI": "rsi",
                "MACD": "macd",
                "MACD_Signal": "macd_signal"
            }

            indicator_key = indicator_map.get(indicator, indicator.lower())
            current_value = latest.get(indicator_key)

            if current_value is None:
                result["error"] = f"Indicator {indicator} not available"
                return result

            result["current_value"] = current_value

            # Check condition
            triggered = False
            signal = None

            if condition == "above" and current_value > threshold:
                triggered = True
                signal = "OVERBOUGHT" if indicator == "RSI" else "ABOVE_THRESHOLD"
            elif condition == "below" and current_value < threshold:
                triggered = True
                signal = "OVERSOLD" if indicator == "RSI" else "BELOW_THRESHOLD"

            if triggered:
                result["triggered"] = True
                result["signal"] = signal
                self.logger.info(
                    f"Technical alert triggered for {ticker}: "
                    f"{indicator}={current_value:.2f} {condition} {threshold:.2f}"
                )

                # Send notification
                if notification_email and self.email_service.enabled:
                    self.email_service.send_technical_alert(
                        to_email=notification_email,
                        ticker=ticker,
                        signal=signal,
                        indicator=indicator,
                        value=current_value
                    )

        except Exception as e:
            self.logger.error(f"Error checking technical alert for {ticker}: {str(e)}")
            result["error"] = str(e)

        return result

    def check_watchlist_alerts(
        self,
        watchlist: List[Dict[str, Any]],
        notification_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Check alerts for all items in watchlist.

        Args:
            watchlist: List of watchlist items with ticker, target_price, stop_loss
            notification_email: Email to send notifications to

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        for item in watchlist:
            ticker = item.get("ticker")
            target_price = item.get("target_price")
            stop_loss = item.get("stop_loss")

            if not ticker:
                continue

            # Check price alerts
            if target_price or stop_loss:
                result = self.check_price_alert(
                    ticker=ticker,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    notification_email=notification_email
                )

                if result.get("triggered"):
                    triggered_alerts.append(result)

            # Small delay to avoid rate limiting
            time.sleep(1)

        return triggered_alerts

    def start_monitoring(
        self,
        watchlist: List[Dict[str, Any]],
        notification_email: Optional[str] = None
    ):
        """
        Start monitoring alerts in background.

        Args:
            watchlist: List of watchlist items
            notification_email: Email for notifications
        """
        def check_alerts():
            """Scheduled task to check alerts."""
            self.logger.info("Checking alerts...")
            alerts = self.check_watchlist_alerts(watchlist, notification_email)
            if alerts:
                self.logger.info(f"Found {len(alerts)} triggered alerts")

        # Schedule the check
        schedule.every(self.check_interval).minutes.do(check_alerts)

        # Run in background thread
        def run_scheduler():
            self._running = True
            while self._running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute if jobs are due

        self._thread = Thread(target=run_scheduler, daemon=True)
        self._thread.start()
        self.logger.info(f"Alert monitoring started (checking every {self.check_interval} minutes)")

    def stop_monitoring(self):
        """Stop monitoring alerts."""
        self._running = False
        schedule.clear()
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Alert monitoring stopped")

    def create_rsi_alerts(
        self,
        tickers: List[str],
        overbought_threshold: float = 70,
        oversold_threshold: float = 30,
        notification_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create RSI alerts for multiple tickers.

        Args:
            tickers: List of ticker symbols
            overbought_threshold: RSI overbought threshold
            oversold_threshold: RSI oversold threshold
            notification_email: Email for notifications

        Returns:
            List of alert results
        """
        results = []

        for ticker in tickers:
            # Check overbought
            result_ob = self.check_technical_alert(
                ticker=ticker,
                indicator="RSI",
                condition="above",
                threshold=overbought_threshold,
                notification_email=notification_email
            )
            if result_ob.get("triggered"):
                results.append(result_ob)

            # Check oversold
            result_os = self.check_technical_alert(
                ticker=ticker,
                indicator="RSI",
                condition="below",
                threshold=oversold_threshold,
                notification_email=notification_email
            )
            if result_os.get("triggered"):
                results.append(result_os)

            time.sleep(1)  # Rate limiting

        return results
