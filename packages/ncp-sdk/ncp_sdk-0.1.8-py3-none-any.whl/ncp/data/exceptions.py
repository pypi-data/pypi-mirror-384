"""Exceptions for the NCP Data module."""


class MetricsError(Exception):
    """Base exception for all metrics-related errors."""

    pass


class MetricsQueryError(MetricsError):
    """Raised when a query fails to execute."""

    pass


class InvalidFilterError(MetricsError):
    """Raised when an invalid filter parameter is provided."""

    pass


class DatabaseConnectionError(MetricsError):
    """Raised when database connection fails."""

    pass


class AggregationError(MetricsError):
    """Raised when time-series aggregation fails."""

    pass


class TimeRangeError(MetricsError):
    """Raised when an invalid time range is specified."""

    pass
