# -*- coding: utf-8 -*-

"""
Core DateTime - Python datetime utilities for time window generation.

This package provides utilities for working with datetime objects, specifically
for generating time windows at various frequencies (hourly, daily, monthly).
All utilities are designed to work with Python 3.12+ without using deprecated
datetime methods.

Main Features:
  - Generate time windows at HOUR, DAY, or MONTH frequency
  - Full timezone support for both naive and aware datetime objects
  - Python 3.12+ compatible (no deprecated datetime.utcnow() usage)
  - Type-safe with comprehensive type hints
  - 100% test coverage

Example Usage:
    >>> from core_datetime import get_time_windows, FrequencyType
    >>> from datetime import timezone
    >>>
    >>> # Generate hourly windows
    >>> windows = get_time_windows(
    ...     start="2022-03-01T10:00:00",
    ...     end="2022-03-01T13:00:00",
    ...     frequency=FrequencyType.HOUR,
    ...     tz=timezone.utc
    ... )
    >>> list(windows)
    [('2022-03-01T10:00:00', '2022-03-01T10:59:59'),
     ('2022-03-01T11:00:00', '2022-03-01T11:59:59'),
     ('2022-03-01T12:00:00', '2022-03-01T12:59:59')]

Available Classes:
    FrequencyType: Enum for specifying time window frequency (HOUR, DAY, MONTH)

Available Functions:
    get_time_windows: Generate time windows between start and end dates
"""

from .utils import FrequencyType
from .utils import get_time_windows

__version__ = "1.1.0"

__all__ = [
    "FrequencyType",
    "get_time_windows",
]
