import logging
from datetime import UTC, datetime

_logger = logging.getLogger(__name__)


def as_local(time: datetime | None) -> datetime | None:
    """
    Converts a foreign time to local time.
    If the time has no timezone, it is assumed to be in UTC. If it does have a timezone, it is converted appropriately.
    If the time is None, None is returned.
    :param time: The time to convert.
    :return: The time as local time, or None
    """
    if time is None:
        return None
    elif time.tzinfo is None:
        return time.replace(tzinfo=UTC).astimezone()
    else:
        return time.astimezone()
