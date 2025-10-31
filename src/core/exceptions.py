"""Custom exceptions for IMP application."""


class IMPException(Exception):
    """Base exception for IMP application."""
    pass


class DataFetchError(IMPException):
    """Raised when data fetching fails."""
    pass


class InvalidTickerError(IMPException):
    """Raised when ticker symbol is invalid."""
    pass


class DatabaseError(IMPException):
    """Raised when database operation fails."""
    pass


class PortfolioError(IMPException):
    """Raised when portfolio operation fails."""
    pass


class ConfigurationError(IMPException):
    """Raised when configuration is invalid."""
    pass


class InsufficientDataError(IMPException):
    """Raised when there is not enough data for analysis."""
    pass
