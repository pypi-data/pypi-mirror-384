import warnings
from datetime import UTC, datetime, timedelta, tzinfo

_THE_EPOCH = datetime.fromtimestamp(0, tz=UTC)


def local_tz() -> tzinfo:
    """Determine this machine's local timezone."""
    tz = datetime.now().astimezone().tzinfo
    if tz is None:
        raise ValueError("Could not determine this machine's local timezone.")
    return tz


def timestamp_micros(instant: datetime) -> int:
    """The number of microseconds between the epoch and the given instant."""
    if instant.tzinfo is None:
        warnings.warn("assuming timezone-naive datetime is local time", stacklevel=2)
        instant = instant.replace(tzinfo=local_tz())
    return (instant - _THE_EPOCH) // timedelta(microseconds=1)


def from_timestamp_micros(ts: int) -> datetime:
    """Convert a timestamp in microseconds to a datetime."""
    if ts < 0:
        raise ValueError("Timestamp must be non-negative")
    return _THE_EPOCH + timedelta(microseconds=ts)
