"""Tests for TechnicalIndicators module."""

import pytest
import pandas as pd
import numpy as np
from src.analysis.technical_indicators import TechnicalIndicators
from src.core.exceptions import InsufficientDataError


class TestTechnicalIndicators:
    """Test cases for TechnicalIndicators class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.indicators = TechnicalIndicators()

        # Create sample data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)

        self.sample_df = pd.DataFrame({
            "Open": 100 + np.random.randn(100).cumsum(),
            "High": 105 + np.random.randn(100).cumsum(),
            "Low": 95 + np.random.randn(100).cumsum(),
            "Close": 100 + np.random.randn(100).cumsum(),
            "Volume": np.random.randint(1000000, 10000000, 100)
        }, index=dates)

        # Ensure High is highest and Low is lowest
        self.sample_df["High"] = self.sample_df[["Open", "High", "Close"]].max(axis=1) + 1
        self.sample_df["Low"] = self.sample_df[["Open", "Low", "Close"]].min(axis=1) - 1

    def test_calculate_sma(self):
        """Test Simple Moving Average calculation."""
        sma = self.indicators.calculate_sma(self.sample_df, period=20)

        assert isinstance(sma, pd.Series)
        assert len(sma) == len(self.sample_df)
        # First 19 values should be NaN
        assert pd.isna(sma.iloc[0:19]).all()
        # After period, should have values
        assert not pd.isna(sma.iloc[20:]).any()

    def test_calculate_ema(self):
        """Test Exponential Moving Average calculation."""
        ema = self.indicators.calculate_ema(self.sample_df, period=20)

        assert isinstance(ema, pd.Series)
        assert len(ema) == len(self.sample_df)
        # EMA should have values after warmup period
        assert not pd.isna(ema.iloc[20:]).any()

    def test_calculate_rsi(self):
        """Test RSI calculation."""
        rsi = self.indicators.calculate_rsi(self.sample_df, period=14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(self.sample_df)
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_calculate_macd(self):
        """Test MACD calculation."""
        macd, signal, histogram = self.indicators.calculate_macd(self.sample_df)

        assert isinstance(macd, pd.Series)
        assert isinstance(signal, pd.Series)
        assert isinstance(histogram, pd.Series)
        assert len(macd) == len(self.sample_df)

        # Histogram should be difference of MACD and signal
        diff = (macd - signal).dropna()
        hist_values = histogram.dropna()
        np.testing.assert_array_almost_equal(diff.values, hist_values.values)

    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        upper, middle, lower = self.indicators.calculate_bollinger_bands(self.sample_df, period=20)

        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)

        # Upper should be greater than middle, middle greater than lower
        valid_data = self.sample_df.iloc[20:]
        assert (upper.iloc[20:] > middle.iloc[20:]).all()
        assert (middle.iloc[20:] > lower.iloc[20:]).all()

    def test_calculate_atr(self):
        """Test Average True Range calculation."""
        atr = self.indicators.calculate_atr(self.sample_df, period=14)

        assert isinstance(atr, pd.Series)
        assert len(atr) == len(self.sample_df)
        # ATR should be positive
        valid_atr = atr.dropna()
        assert (valid_atr > 0).all()

    def test_insufficient_data_error(self):
        """Test error handling for insufficient data."""
        small_df = self.sample_df.iloc[:5]

        with pytest.raises(InsufficientDataError):
            self.indicators.calculate_sma(small_df, period=20)

    def test_calculate_all_indicators(self):
        """Test calculating all indicators at once."""
        result_df = self.indicators.calculate_all_indicators(self.sample_df)

        assert isinstance(result_df, pd.DataFrame)
        # Should have original columns plus indicator columns
        assert len(result_df.columns) > len(self.sample_df.columns)

        # Check for key indicator columns
        assert "RSI" in result_df.columns
        assert "MACD" in result_df.columns
        assert "BB_Upper" in result_df.columns
        assert "SMA_20" in result_df.columns
