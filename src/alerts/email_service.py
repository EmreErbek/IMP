"""Email notification service for alerts."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

from ..core.logger import IMPLogger
from ..core.exceptions import IMPException


class EmailServiceError(IMPException):
    """Raised when email sending fails."""
    pass


class EmailService:
    """Service for sending email notifications."""

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize EmailService.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            sender_email: Sender email address
            sender_password: Sender email password/app password
            enabled: Whether email service is enabled
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.enabled = enabled and sender_email and sender_password
        self.logger = IMPLogger.get_logger()

        if not self.enabled:
            self.logger.warning("Email service is disabled. Configure SMTP settings to enable.")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            html: Whether body is HTML

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.warning("Email service is disabled. Email not sent.")
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            # Add body
            mime_type = "html" if html else "plain"
            message.attach(MIMEText(body, mime_type))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            self.logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False

    def send_price_alert(
        self,
        to_email: str,
        ticker: str,
        current_price: float,
        target_price: float,
        alert_type: str
    ) -> bool:
        """
        Send a price alert email.

        Args:
            to_email: Recipient email
            ticker: Ticker symbol
            current_price: Current stock price
            target_price: Target/stop loss price
            alert_type: Type of alert (TARGET_HIT, STOP_LOSS_HIT)

        Returns:
            True if sent successfully
        """
        if alert_type == "TARGET_HIT":
            subject = f"🎯 Price Target Hit: {ticker}"
            message = f"""
                <h2>Price Target Alert</h2>
                <p><strong>{ticker}</strong> has reached your target price!</p>
                <ul>
                    <li><strong>Current Price:</strong> {current_price:.2f} TRY</li>
                    <li><strong>Target Price:</strong> {target_price:.2f} TRY</li>
                    <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                <p>Consider taking action on your position.</p>
            """
        else:  # STOP_LOSS_HIT
            subject = f"⚠️ Stop Loss Hit: {ticker}"
            message = f"""
                <h2>Stop Loss Alert</h2>
                <p><strong>{ticker}</strong> has hit your stop loss price!</p>
                <ul>
                    <li><strong>Current Price:</strong> {current_price:.2f} TRY</li>
                    <li><strong>Stop Loss:</strong> {target_price:.2f} TRY</li>
                    <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                <p style="color: red;"><strong>Consider exiting your position to limit losses.</strong></p>
            """

        return self.send_email(to_email, subject, message, html=True)

    def send_technical_alert(
        self,
        to_email: str,
        ticker: str,
        signal: str,
        indicator: str,
        value: float
    ) -> bool:
        """
        Send a technical indicator alert email.

        Args:
            to_email: Recipient email
            ticker: Ticker symbol
            signal: Signal type (OVERBOUGHT, OVERSOLD, BULLISH_CROSSOVER, etc.)
            indicator: Indicator name (RSI, MACD, etc.)
            value: Indicator value

        Returns:
            True if sent successfully
        """
        subject = f"📊 Technical Signal: {ticker} - {signal}"

        signal_descriptions = {
            "OVERBOUGHT": "is in overbought territory. Consider taking profits.",
            "OVERSOLD": "is in oversold territory. Consider buying opportunity.",
            "BULLISH_CROSSOVER": "shows a bullish crossover. Potential buy signal.",
            "BEARISH_CROSSOVER": "shows a bearish crossover. Potential sell signal."
        }

        description = signal_descriptions.get(signal, "has triggered an alert.")

        message = f"""
            <h2>Technical Analysis Alert</h2>
            <p><strong>{ticker}</strong> {description}</p>
            <ul>
                <li><strong>Indicator:</strong> {indicator}</li>
                <li><strong>Signal:</strong> {signal}</li>
                <li><strong>Value:</strong> {value:.2f}</li>
                <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            <p>Review the stock's technical analysis for more details.</p>
        """

        return self.send_email(to_email, subject, message, html=True)

    def send_portfolio_summary(
        self,
        to_email: str,
        summary_data: dict
    ) -> bool:
        """
        Send portfolio summary email.

        Args:
            to_email: Recipient email
            summary_data: Portfolio summary dictionary

        Returns:
            True if sent successfully
        """
        subject = f"📈 Portfolio Summary - {datetime.now().strftime('%Y-%m-%d')}"

        total_pl = summary_data.get("total_profit_loss", 0)
        pl_color = "green" if total_pl >= 0 else "red"

        message = f"""
            <h2>Your Portfolio Summary</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Positions</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{summary_data.get('total_positions', 0)}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Invested</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{summary_data.get('total_invested', 0):.2f} TRY</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Current Value</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{summary_data.get('current_value', 0):.2f} TRY</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total P&L</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: {pl_color};"><strong>{total_pl:.2f} TRY</strong></td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Return %</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: {pl_color};"><strong>{summary_data.get('return_percentage', 0):.2f}%</strong></td>
                </tr>
            </table>
            <p><small>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        """

        return self.send_email(to_email, subject, message, html=True)
