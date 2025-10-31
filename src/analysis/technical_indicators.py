"""Technical indicators for stock analysis."""

import pandas as pd
import numpy as np
from typing import Tuple, Optional

from ..core.exceptions import InsufficientDataError
from ..core.logger import IMPLogger


class TechnicalIndicators:
    """Calculate various technical indicators for stock analysis."""

    def __init__(self):
        """Initialize TechnicalIndicators."""
        self.logger = IMPLogger.get_logger()

    @staticmethod
    def _validate_data(df: pd.DataFrame, min_periods: int):
        """Validate if DataFrame has sufficient data."""
        if df is None or df.empty:
            raise InsufficientDataError("DataFrame is empty")
        if len(df) < min_periods:
            raise InsufficientDataError(
                f"Insufficient data. Need at least {min_periods} periods, got {len(df)}"
            )

    def calculate_sma(self, df: pd.DataFrame, period: int = 20, column: str = "Close") -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            df: DataFrame with stock data
            period: Period for SMA calculation
            column: Column to calculate SMA on

        Returns:
            Series with SMA values
        """
        self._validate_data(df, period)
        return df[column].rolling(window=period).mean()

    def calculate_ema(self, df: pd.DataFrame, period: int = 20, column: str = "Close") -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            df: DataFrame with stock data
            period: Period for EMA calculation
            column: Column to calculate EMA on

        Returns:
            Series with EMA values
        """
        self._validate_data(df, period)
        return df[column].ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14, column: str = "Close") -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            df: DataFrame with stock data
            period: Period for RSI calculation
            column: Column to calculate RSI on

        Returns:
            Series with RSI values (0-100)
        """
        self._validate_data(df, period + 1)

        # Calculate price changes
        delta = df[column].diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "Close"
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            df: DataFrame with stock data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            column: Column to calculate MACD on

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        self._validate_data(df, slow_period + signal_period)

        # Calculate EMAs
        ema_fast = self.calculate_ema(df, fast_period, column)
        ema_slow = self.calculate_ema(df, slow_period, column)

        # MACD line
        macd_line = ema_fast - ema_slow

        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = "Close"
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.

        Args:
            df: DataFrame with stock data
            period: Period for moving average
            std_dev: Number of standard deviations
            column: Column to calculate bands on

        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        self._validate_data(df, period)

        # Middle band (SMA)
        middle_band = self.calculate_sma(df, period, column)

        # Standard deviation
        std = df[column].rolling(window=period).std()

        # Upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return upper_band, middle_band, lower_band

    def calculate_stochastic(
        self,
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.

        Args:
            df: DataFrame with stock data
            k_period: Period for %K line
            d_period: Period for %D line (signal)

        Returns:
            Tuple of (%K line, %D line)
        """
        self._validate_data(df, k_period)

        # Calculate %K
        low_min = df["Low"].rolling(window=k_period).min()
        high_max = df["High"].rolling(window=k_period).max()

        k_line = 100 * ((df["Close"] - low_min) / (high_max - low_min))

        # Calculate %D (signal line)
        d_line = k_line.rolling(window=d_period).mean()

        return k_line, d_line

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR).

        Args:
            df: DataFrame with stock data
            period: Period for ATR calculation

        Returns:
            Series with ATR values
        """
        self._validate_data(df, period)

        # Calculate True Range
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Calculate ATR
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV).

        Args:
            df: DataFrame with stock data

        Returns:
            Series with OBV values
        """
        self._validate_data(df, 2)

        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df["Volume"].iloc[0]

        for i in range(1, len(df)):
            if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] + df["Volume"].iloc[i]
            elif df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] - df["Volume"].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]

        return obv

    def calculate_all_indicators(
        self,
        df: pd.DataFrame,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        sma_periods: list = [20, 50, 200]
    ) -> pd.DataFrame:
        """
        Calculate all technical indicators and add them to DataFrame.

        Args:
            df: DataFrame with stock data
            rsi_period: RSI period
            macd_fast: MACD fast period
            macd_slow: MACD slow period
            macd_signal: MACD signal period
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation
            sma_periods: List of SMA periods to calculate

        Returns:
            DataFrame with all indicators added
        """
        result_df = df.copy()

        try:
            # RSI
            result_df["RSI"] = self.calculate_rsi(df, rsi_period)

            # MACD
            macd, signal, hist = self.calculate_macd(df, macd_fast, macd_slow, macd_signal)
            result_df["MACD"] = macd
            result_df["MACD_Signal"] = signal
            result_df["MACD_Hist"] = hist

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df, bb_period, bb_std)
            result_df["BB_Upper"] = bb_upper
            result_df["BB_Middle"] = bb_middle
            result_df["BB_Lower"] = bb_lower

            # Moving Averages
            for period in sma_periods:
                if len(df) >= period:
                    result_df[f"SMA_{period}"] = self.calculate_sma(df, period)
                    result_df[f"EMA_{period}"] = self.calculate_ema(df, period)

            # Stochastic
            stoch_k, stoch_d = self.calculate_stochastic(df)
            result_df["Stoch_K"] = stoch_k
            result_df["Stoch_D"] = stoch_d

            # ATR
            result_df["ATR"] = self.calculate_atr(df)

            # OBV
            result_df["OBV"] = self.calculate_obv(df)

            self.logger.info("Successfully calculated all technical indicators")

        except Exception as e:
            self.logger.warning(f"Error calculating some indicators: {str(e)}")

        return result_df
