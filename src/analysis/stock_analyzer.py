"""Stock analysis module with technical analysis."""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.data_fetcher import DataFetcher
from ..core.logger import IMPLogger
from .technical_indicators import TechnicalIndicators


class StockAnalyzer:
    """Analyze stocks using technical indicators and provide insights."""

    def __init__(self, data_fetcher: Optional[DataFetcher] = None):
        """
        Initialize StockAnalyzer.

        Args:
            data_fetcher: DataFetcher instance (creates new one if not provided)
        """
        self.data_fetcher = data_fetcher or DataFetcher()
        self.indicators = TechnicalIndicators()
        self.logger = IMPLogger.get_logger()

    def analyze_stock(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on a stock.

        Args:
            ticker: Ticker symbol
            period: Data period
            interval: Data interval

        Returns:
            Dictionary with analysis results
        """
        self.logger.info(f"Starting analysis for {ticker}")

        # Fetch data
        df = self.data_fetcher.get_stock_data(ticker, period, interval)

        # Calculate all indicators
        df_with_indicators = self.indicators.calculate_all_indicators(df)

        # Get latest values
        latest = df_with_indicators.iloc[-1]
        previous = df_with_indicators.iloc[-2] if len(df_with_indicators) > 1 else None

        # Perform analysis
        analysis = {
            "ticker": ticker,
            "analysis_date": datetime.now().isoformat(),
            "data_period": period,
            "latest_data": self._get_latest_data(latest, previous),
            "technical_signals": self._analyze_technical_signals(df_with_indicators),
            "trend_analysis": self._analyze_trend(df_with_indicators),
            "volatility": self._calculate_volatility(df_with_indicators),
            "summary": {}
        }

        # Generate summary
        analysis["summary"] = self._generate_summary(analysis)

        self.logger.info(f"Completed analysis for {ticker}")
        return analysis

    def _get_latest_data(
        self,
        latest: pd.Series,
        previous: Optional[pd.Series]
    ) -> Dict[str, Any]:
        """Extract latest price and indicator data."""
        data = {
            "close": float(latest["Close"]),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "volume": int(latest["Volume"]),
        }

        if previous is not None:
            data["price_change"] = float(latest["Close"] - previous["Close"])
            data["price_change_pct"] = float(
                ((latest["Close"] - previous["Close"]) / previous["Close"]) * 100
            )

        # Add indicator values
        if "RSI" in latest and pd.notna(latest["RSI"]):
            data["rsi"] = float(latest["RSI"])
        if "MACD" in latest and pd.notna(latest["MACD"]):
            data["macd"] = float(latest["MACD"])
            data["macd_signal"] = float(latest["MACD_Signal"])
        if "BB_Upper" in latest and pd.notna(latest["BB_Upper"]):
            data["bb_upper"] = float(latest["BB_Upper"])
            data["bb_middle"] = float(latest["BB_Middle"])
            data["bb_lower"] = float(latest["BB_Lower"])

        return data

    def _analyze_technical_signals(self, df: pd.DataFrame) -> Dict[str, str]:
        """Analyze technical indicators and generate signals."""
        signals = {}
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else None

        # RSI signals
        if "RSI" in df.columns and pd.notna(latest["RSI"]):
            rsi = latest["RSI"]
            if rsi < 30:
                signals["rsi"] = "OVERSOLD"
            elif rsi > 70:
                signals["rsi"] = "OVERBOUGHT"
            else:
                signals["rsi"] = "NEUTRAL"

        # MACD signals
        if "MACD" in df.columns and pd.notna(latest["MACD"]) and previous is not None:
            if latest["MACD"] > latest["MACD_Signal"] and previous["MACD"] <= previous["MACD_Signal"]:
                signals["macd"] = "BULLISH_CROSSOVER"
            elif latest["MACD"] < latest["MACD_Signal"] and previous["MACD"] >= previous["MACD_Signal"]:
                signals["macd"] = "BEARISH_CROSSOVER"
            elif latest["MACD"] > latest["MACD_Signal"]:
                signals["macd"] = "BULLISH"
            else:
                signals["macd"] = "BEARISH"

        # Bollinger Bands signals
        if "BB_Upper" in df.columns and pd.notna(latest["BB_Upper"]):
            close = latest["Close"]
            if close > latest["BB_Upper"]:
                signals["bollinger"] = "OVERBOUGHT"
            elif close < latest["BB_Lower"]:
                signals["bollinger"] = "OVERSOLD"
            else:
                signals["bollinger"] = "NEUTRAL"

        # Stochastic signals
        if "Stoch_K" in df.columns and pd.notna(latest["Stoch_K"]):
            stoch_k = latest["Stoch_K"]
            if stoch_k < 20:
                signals["stochastic"] = "OVERSOLD"
            elif stoch_k > 80:
                signals["stochastic"] = "OVERBOUGHT"
            else:
                signals["stochastic"] = "NEUTRAL"

        return signals

    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trends using moving averages."""
        trend = {}
        latest = df.iloc[-1]

        # Short-term trend (SMA 20 vs SMA 50)
        if "SMA_20" in df.columns and "SMA_50" in df.columns:
            if pd.notna(latest["SMA_20"]) and pd.notna(latest["SMA_50"]):
                if latest["SMA_20"] > latest["SMA_50"]:
                    trend["short_term"] = "UPTREND"
                else:
                    trend["short_term"] = "DOWNTREND"

        # Long-term trend (SMA 50 vs SMA 200)
        if "SMA_50" in df.columns and "SMA_200" in df.columns:
            if pd.notna(latest["SMA_50"]) and pd.notna(latest["SMA_200"]):
                if latest["SMA_50"] > latest["SMA_200"]:
                    trend["long_term"] = "UPTREND"
                else:
                    trend["long_term"] = "DOWNTREND"

        # Price vs moving averages
        close = latest["Close"]
        if "SMA_20" in df.columns and pd.notna(latest["SMA_20"]):
            trend["price_vs_sma20"] = "ABOVE" if close > latest["SMA_20"] else "BELOW"
        if "SMA_50" in df.columns and pd.notna(latest["SMA_50"]):
            trend["price_vs_sma50"] = "ABOVE" if close > latest["SMA_50"] else "BELOW"
        if "SMA_200" in df.columns and pd.notna(latest["SMA_200"]):
            trend["price_vs_sma200"] = "ABOVE" if close > latest["SMA_200"] else "BELOW"

        return trend

    def _calculate_volatility(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate volatility metrics."""
        volatility = {}

        # Daily returns
        returns = df["Close"].pct_change()

        # Standard deviation of returns (volatility)
        volatility["daily_volatility"] = float(returns.std())
        volatility["annualized_volatility"] = float(returns.std() * (252 ** 0.5))

        # Average True Range (ATR) based volatility
        if "ATR" in df.columns:
            latest_atr = df["ATR"].iloc[-1]
            if pd.notna(latest_atr):
                volatility["atr"] = float(latest_atr)
                volatility["atr_percentage"] = float(
                    (latest_atr / df["Close"].iloc[-1]) * 100
                )

        return volatility

    def _generate_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary and recommendation."""
        signals = analysis["technical_signals"]
        trend = analysis["trend_analysis"]

        # Count bullish and bearish signals
        bullish_count = 0
        bearish_count = 0

        # RSI
        if signals.get("rsi") == "OVERSOLD":
            bullish_count += 1
        elif signals.get("rsi") == "OVERBOUGHT":
            bearish_count += 1

        # MACD
        if "BULLISH" in signals.get("macd", ""):
            bullish_count += 1
        elif "BEARISH" in signals.get("macd", ""):
            bearish_count += 1

        # Bollinger Bands
        if signals.get("bollinger") == "OVERSOLD":
            bullish_count += 1
        elif signals.get("bollinger") == "OVERBOUGHT":
            bearish_count += 1

        # Trend
        if trend.get("short_term") == "UPTREND":
            bullish_count += 1
        elif trend.get("short_term") == "DOWNTREND":
            bearish_count += 1

        if trend.get("long_term") == "UPTREND":
            bullish_count += 1
        elif trend.get("long_term") == "DOWNTREND":
            bearish_count += 1

        # Generate overall signal
        if bullish_count > bearish_count + 1:
            overall = "BULLISH"
        elif bearish_count > bullish_count + 1:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"

        return {
            "overall_signal": overall,
            "bullish_indicators": bullish_count,
            "bearish_indicators": bearish_count,
            "confidence": abs(bullish_count - bearish_count) / max(bullish_count + bearish_count, 1)
        }

    def compare_stocks(
        self,
        tickers: list,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Compare multiple stocks.

        Args:
            tickers: List of ticker symbols
            period: Data period

        Returns:
            DataFrame with comparison data
        """
        comparison_data = []

        for ticker in tickers:
            try:
                analysis = self.analyze_stock(ticker, period)
                latest = analysis["latest_data"]
                signals = analysis["technical_signals"]
                summary = analysis["summary"]

                comparison_data.append({
                    "Ticker": ticker,
                    "Price": latest.get("close"),
                    "Change %": latest.get("price_change_pct"),
                    "RSI": latest.get("rsi"),
                    "RSI Signal": signals.get("rsi"),
                    "MACD Signal": signals.get("macd"),
                    "Overall": summary.get("overall_signal"),
                    "Confidence": f"{summary.get('confidence', 0) * 100:.1f}%"
                })
            except Exception as e:
                self.logger.error(f"Failed to analyze {ticker}: {str(e)}")

        return pd.DataFrame(comparison_data)
