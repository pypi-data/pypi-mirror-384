# -*- coding: utf-8 -*-

"""
DateTime utilities for time window generation and date manipulation.

This module provides utilities for generating time windows at various frequencies
(hourly, daily, monthly) with optional timezone support. All functions are designed
to work with Python 3.12+ without using deprecated datetime methods.
"""

from calendar import monthrange
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Tuple, Iterator, Optional

from dateutil.rrule import MONTHLY  # type: ignore[import-untyped]
from dateutil.rrule import rrule  # type: ignore[import-untyped]


class FrequencyType(Enum):
    """
    Enumeration of supported time window frequencies.

    Attributes:
        HOUR: Generate hourly time windows (HH:00:00 to HH:59:59)
        DAY: Generate daily time windows (00:00:00 to 23:59:59)
        MONTH: Generate monthly time windows (first day to last day of month)
    """

    HOUR = "HOUR"
    MONTH = "MONTH"
    DAY = "DAY"



def get_time_windows(
    start: str,
    end: Optional[str] = None,
    frequency: Optional[FrequencyType] = None,
    tz: Optional[timezone] = None,
) -> Iterator[Tuple[str, str]]:
    """
    Generate time windows between start and end dates at specified
    frequency. This function generates tuples of (start_time, end_time) strings
    representing consecutive time windows based on the specified frequency. If
    no frequency is provided, returns a single tuple with
    the start time and current time.

    :param start:
        ISO format datetime string (e.g., "2022-03-01T10:30:00").
        Can be timezone-aware or naive.

    :param end:
        ISO format datetime string for the end boundary. If None, uses
        current time. Defaults to None.

    :param frequency:
        Time window frequency (HOUR, DAY, or MONTH). If None, returns
        a single window from start to now. Defaults to None.

    :param tz:
        Timezone to apply to naive datetime strings. If the input strings
        already contain timezone info, this parameter is ignored for those
        values. Defaults to None (naive/local time).

    :returns:
        Iterator of tuples containing (start_time, end_time) strings in ISO format.
          - HOUR frequency: Returns windows like ("2022-03-01T10:00:00", "2022-03-01T10:59:59")
          - DAY frequency: Returns windows like ("2022-03-01T00:00:00", "2022-03-01T23:59:59")
          - MONTH frequency: Returns windows like ("2022-03-01T00:00:00", "2022-03-31T23:59:59")

    Examples:
        >>> # Generate hourly windows for the last 3 hours
        >>> start = (datetime.now() - timedelta(hours=3)).isoformat()
        >>> for window in get_time_windows(start, frequency=FrequencyType.HOUR):
        ...     print(window)
        ('2022-03-01T10:00:00', '2022-03-01T10:59:59')
        ('2022-03-01T11:00:00', '2022-03-01T11:59:59')
        ('2022-03-01T12:00:00', '2022-03-01T12:59:59')

        >>> # Generate monthly windows with explicit end date
        >>> windows = get_time_windows(
        ...     start="2022-01-01T00:00:00",
        ...     end="2022-04-01T00:00:00",
        ...     frequency=FrequencyType.MONTH
        ... )
        >>> list(windows)
        [('2022-01-01T00:00:00', '2022-01-31T23:59:59'),
         ('2022-02-01T00:00:00', '2022-02-28T23:59:59'),
         ('2022-03-01T00:00:00', '2022-03-31T23:59:59')]

        >>> # Use timezone-aware datetimes
        >>> from datetime import timezone
        >>> windows = get_time_windows(
        ...     start="2022-03-01T00:00:00",
        ...     end="2022-03-02T00:00:00",
        ...     frequency=FrequencyType.DAY,
        ...     tz=timezone.utc
        ... )

    Note:
      - Minutes and seconds are normalized to :00:00 for the start time
      - For HOUR frequency, end times are set to :59:59 of the same hour
      - For DAY frequency, end times are set to 23:59:59 of the same day
      - For MONTH frequency, end times are set to 23:59:59 of the last day
      - Timezone-aware and naive datetimes cannot be mixed; if tz is provided,
        it will be applied to any naive input strings
    """

    now_ = datetime.now(tz=tz)
    if not frequency:
        yield start, now_.strftime("%Y-%m-%dT%H:%M:%S")

    start_dt = datetime.fromisoformat(start).replace(
        minute=0,
        second=0,
        microsecond=0)

    if tz and start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tz)

    end_dt = (now_ if not end else datetime.fromisoformat(end)).replace(
        minute=0,
        second=0,
        microsecond=0)

    if tz and end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=tz)

    if frequency in [FrequencyType.HOUR, FrequencyType.DAY]:
        if frequency == FrequencyType.HOUR:
            delta = timedelta(hours=1)

        else:
            start_dt, end_dt = start_dt.replace(hour=0), end_dt.replace(hour=0)
            delta = timedelta(days=1)

        while start_dt < end_dt and (start_dt + delta) <= end_dt:
            start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
            if frequency == FrequencyType.HOUR:
                end_str = start_dt.strftime("%Y-%m-%dT%H:59:59")
            else:
                end_str = start_dt.strftime("%Y-%m-%dT23:59:59")

            yield start_str, end_str
            start_dt = start_dt + delta

    elif frequency == FrequencyType.MONTH:
        end_dt = end_dt.replace(hour=0)

        for d in rrule(MONTHLY, dtstart=start_dt, until=end_dt):
            start_ = datetime(
                year=d.year,
                month=d.month,
                day=1,
                tzinfo=tz if tz else start_dt.tzinfo,)

            end_ = start_.replace(day=monthrange(start_.year, start_.month)[1])
            if end_ <= end_dt:
                yield start_.strftime("%Y-%m-%dT%H:%M:%S"), end_.strftime("%Y-%m-%dT23:59:59")
