"""NCP Data Module - Metrics API Type Stubs

This module provides type hints and method signatures for the Metrics API.
The actual implementation is provided by the NCP platform at runtime.

Key Features:
- Type hints for all metric query methods
- IDE autocomplete support
- Documentation for all methods and parameters
- No actual database dependencies required

Usage:
    >>> from ncp.data import Metrics
    >>> # Or
    >>> from ncp import Metrics
    >>>
    >>> # IDE will show all available methods with autocomplete
    >>> metrics = Metrics()  # Works only on platform
    >>> devices = metrics.get_devices(layer="spine")
"""

from .client import Metrics
from .exceptions import (
    MetricsError,
    MetricsQueryError,
    InvalidFilterError,
    DatabaseConnectionError,
    AggregationError,
    TimeRangeError,
)

__all__ = [
    "Metrics",
    "MetricsError",
    "MetricsQueryError",
    "InvalidFilterError",
    "DatabaseConnectionError",
    "AggregationError",
    "TimeRangeError",
]
