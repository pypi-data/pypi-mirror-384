"""A set of utility functions for time handling in logging."""

from datetime import datetime
from typing import TYPE_CHECKING

from bear_epoch_time import DATE_FORMAT, DT_FORMAT_WITH_SECONDS, PT_TIME_ZONE, TIME_FORMAT_WITH_SECONDS, EpochTimestamp
from bear_epoch_time.tz import TimeZoneType, get_local_timezone

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo


class TimeHelper:
    def __init__(
        self,
        fmt: str = DT_FORMAT_WITH_SECONDS,
        date_fmt: str = DATE_FORMAT,
        time_fmt: str = TIME_FORMAT_WITH_SECONDS,
        tz: TimeZoneType = PT_TIME_ZONE,
    ) -> None:
        self.fmt: str = fmt
        self.date_fmt: str = date_fmt
        self.time_fmt: str = time_fmt
        self.tz_pref: TimeZoneType = tz
        self.tz_detected: ZoneInfo = get_local_timezone()

    @property
    def now(self) -> EpochTimestamp:
        """Get the current time as an EpochTimestamp object."""
        return EpochTimestamp.now()

    def get_current_time(
        self,
        fmt: str = TIME_FORMAT_WITH_SECONDS,
        tz: TimeZoneType = PT_TIME_ZONE,
        time_only: bool = True,
    ) -> str:
        """Get the current time as an integer timestamp."""
        fmt = fmt or self.time_fmt if time_only else self.fmt
        tz = tz or self.tz
        return self.now.to_string(fmt=fmt, tz=tz)

    def get_timestamp(
        self,
        fmt: str = DT_FORMAT_WITH_SECONDS,
        tz: TimeZoneType = PT_TIME_ZONE,
        time_only: bool = False,
    ) -> str:
        """Get the current full timestamp as a formatted string."""
        fmt = fmt or self.fmt if not time_only else self.time_fmt
        tz = tz or self.tz
        return self.now.to_string(fmt=fmt, tz=tz)

    def get_datetime(self) -> datetime:
        """Get the current datetime with local timezone if available."""
        dt: datetime = self.now.to_datetime
        return dt.astimezone(self.tz_detected) if self.tz_detected else dt
