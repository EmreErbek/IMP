"""Tests for DataFetcher module."""

import pytest
import pandas as pd
from src.core.data_fetcher import DataFetcher
from src.core.exceptions import DataFetchError, InvalidTickerError, InsufficientDataError


class TestDataFetcher:
    """Test cases for DataFetcher class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.fetcher = DataFetcher(market_suffix=".IS", cache_enabled=False)

    def test_get_full_ticker(self):
        """Test ticker symbol formatting."""
        assert self.fetcher._get_full_ticker("THYAO") == "THYAO.IS"
        assert self.fetcher._get_full_ticker("thyao") == "THYAO.IS"
        assert self.fetcher._get_full_ticker("THYAO.IS") == "THYAO.IS"

    def test_get_stock_data_valid(self):
        """Test fetching valid stock data."""
        # Using a well-known Turkish stock
        df = self.fetcher.get_stock_data("THYAO", period="5d", interval="1d")

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "Close" in df.columns
        assert "Open" in df.columns
        assert "High" in df.columns
        assert "Low" in df.columns
        assert "Volume" in df.columns

    def test_get_stock_data_invalid_ticker(self):
        """Test fetching data with invalid ticker."""
        with pytest.raises((DataFetchError, InsufficientDataError)):
            self.fetcher.get_stock_data("INVALID_TICKER_XYZ", period="1d")

    def test_cache_functionality(self):
        """Test caching mechanism."""
        fetcher_with_cache = DataFetcher(cache_enabled=True)

        # First fetch
        df1 = fetcher_with_cache.get_stock_data("THYAO", period="5d")

        # Second fetch (should use cache)
        df2 = fetcher_with_cache.get_stock_data("THYAO", period="5d")

        pd.testing.assert_frame_equal(df1, df2)

    def test_clear_cache(self):
        """Test cache clearing."""
        fetcher = DataFetcher(cache_enabled=True)

        # Fetch data to populate cache
        fetcher.get_stock_data("THYAO", period="5d")

        assert len(fetcher._cache) > 0

        # Clear cache
        fetcher.clear_cache()

        assert len(fetcher._cache) == 0
