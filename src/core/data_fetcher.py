"""Data fetching module for stock market data."""

import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .exceptions import DataFetchError, InvalidTickerError, InsufficientDataError
from .logger import IMPLogger


class DataFetcher:
    """Fetches stock market data from Yahoo Finance."""

    def __init__(self, market_suffix: str = ".IS", cache_enabled: bool = True):
        """
        Initialize DataFetcher.

        Args:
            market_suffix: Market suffix for ticker symbols (e.g., .IS for Borsa Istanbul)
            cache_enabled: Whether to enable caching
        """
        self.market_suffix = market_suffix
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.logger = IMPLogger.get_logger()

    def _get_full_ticker(self, ticker: str) -> str:
        """
        Get full ticker symbol with market suffix.

        Args:
            ticker: Ticker symbol without suffix

        Returns:
            Full ticker symbol with suffix
        """
        ticker = ticker.upper().strip()
        if not ticker.endswith(self.market_suffix):
            ticker = ticker + self.market_suffix
        return ticker

    def _is_cache_valid(self, ticker: str, cache_hours: int = 24) -> bool:
        """
        Check if cached data is still valid.

        Args:
            ticker: Ticker symbol
            cache_hours: Cache validity duration in hours

        Returns:
            True if cache is valid, False otherwise
        """
        if not self.cache_enabled or ticker not in self._cache:
            return False

        cache_time = self._cache[ticker].get("timestamp")
        if cache_time is None:
            return False

        return datetime.now() - cache_time < timedelta(hours=cache_hours)

    def get_stock_data(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical stock data.

        Args:
            ticker: Ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            use_cache: Whether to use cached data

        Returns:
            DataFrame with historical stock data

        Raises:
            InvalidTickerError: If ticker is invalid
            DataFetchError: If data fetching fails
            InsufficientDataError: If insufficient data is available
        """
        full_ticker = self._get_full_ticker(ticker)
        cache_key = f"{full_ticker}_{period}_{interval}"

        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            self.logger.debug(f"Using cached data for {full_ticker}")
            return self._cache[cache_key]["data"].copy()

        try:
            self.logger.info(f"Fetching data for {full_ticker} (period={period}, interval={interval})")

            stock = yf.Ticker(full_ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                raise InsufficientDataError(
                    f"No data available for ticker {full_ticker}. "
                    "Please check if the ticker symbol is correct."
                )

            # Validate data
            if len(df) < 2:
                raise InsufficientDataError(
                    f"Insufficient data for {full_ticker}. Only {len(df)} records found."
                )

            # Cache data
            if self.cache_enabled:
                self._cache[cache_key] = {
                    "data": df.copy(),
                    "timestamp": datetime.now()
                }

            self.logger.info(f"Successfully fetched {len(df)} records for {full_ticker}")
            return df

        except InsufficientDataError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to fetch data for {full_ticker}: {str(e)}")
            raise DataFetchError(f"Failed to fetch data for {full_ticker}: {str(e)}")

    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get stock information and metadata.

        Args:
            ticker: Ticker symbol

        Returns:
            Dictionary with stock information

        Raises:
            InvalidTickerError: If ticker is invalid
            DataFetchError: If data fetching fails
        """
        full_ticker = self._get_full_ticker(ticker)

        try:
            self.logger.info(f"Fetching info for {full_ticker}")
            stock = yf.Ticker(full_ticker)
            info = stock.info

            if not info or "symbol" not in info:
                raise InvalidTickerError(
                    f"Invalid ticker symbol: {full_ticker}. "
                    "No information available."
                )

            return info

        except InvalidTickerError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to fetch info for {full_ticker}: {str(e)}")
            raise DataFetchError(f"Failed to fetch info for {full_ticker}: {str(e)}")

    def get_multiple_stocks(
        self,
        tickers: list,
        period: str = "1y",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks.

        Args:
            tickers: List of ticker symbols
            period: Data period
            interval: Data interval

        Returns:
            Dictionary mapping tickers to their DataFrames
        """
        results = {}
        failed = []

        for ticker in tickers:
            try:
                results[ticker] = self.get_stock_data(ticker, period, interval)
            except Exception as e:
                self.logger.warning(f"Failed to fetch {ticker}: {str(e)}")
                failed.append(ticker)

        if failed:
            self.logger.warning(f"Failed to fetch data for: {', '.join(failed)}")

        return results

    def clear_cache(self, ticker: Optional[str] = None):
        """
        Clear cached data.

        Args:
            ticker: Specific ticker to clear, or None to clear all
        """
        if ticker:
            full_ticker = self._get_full_ticker(ticker)
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(full_ticker)]
            for key in keys_to_remove:
                del self._cache[key]
            self.logger.info(f"Cleared cache for {full_ticker}")
        else:
            self._cache.clear()
            self.logger.info("Cleared all cache")
