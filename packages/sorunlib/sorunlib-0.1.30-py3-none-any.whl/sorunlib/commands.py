import time
import datetime as dt


def _timestamp_to_utc_datetime(timestamp):
    """Produce a UTC datetime object from a naive or UTC timestamp.

    Args:
        timestamp (str): Time in ISO format and in UTC timezone,
            i.e. "2015-10-21T07:28:00", "2023-01-01T0:00:00+00:00"

    Returns:
        datetime.datetime: datetime object with datetime.timezone.utc tzinfo.

    Raises:
        ValueError: If `timestamp` has an unsupported timezone.

    """
    target = dt.datetime.fromisoformat(timestamp)

    # Effectively pytz.utc.localize(target)
    if target.tzinfo is None:
        target = target.replace(tzinfo=dt.timezone.utc)

    # Check timezone
    if target.tzinfo is not dt.timezone.utc:
        offset = target.tzinfo.tzname(None)
        raise ValueError(f'Unsupported timezone ({offset}) detected. '
                         + 'Timezone must be UTC.')

    return target


def wait_until(timestamp, tolerance=None):
    """Wait until a specified time.

    Args:
        timestamp (str): Time in ISO format and in UTC timezone to wait
            until. If UTC ("+00:00") is not explicitly used in the timestamp it
            is assumed.
        tolerance (int, float, or str): Tolerance on the difference between the
            time when the function is evaluated and `timestamp`. Can be
            specified as a ISO formatted timestamp (str) or in number of
            seconds (int, float).

            When evaluated, if `tolerance` (str) is in the past or if the
            difference between the current time and `timestamp` is greater than
            this `tolerance` (int, float), then an error is raised. If `None`,
            an error will not be raised. Default is `None`.

    Raises:
        ValueError: If `timestamp` has an unsupported timezone, `tolerance`
            is an unsupported type, or if the current time at evaluation is past
            the threshold set by the `tolerance`.

    Examples:
        >>> wait_until("2015-10-21T07:28:00")
        >>> wait_until("2015-10-21T07:28:00+00:00")
        >>> wait_until("2015-10-21T07:28:00+00:00", 60)
        >>> wait_until("2015-10-21T07:28:00+00:00", "2015-10-21T07:29:00+00:00")

    """
    target = _timestamp_to_utc_datetime(timestamp)

    # Grab current UTC timestamp
    now = dt.datetime.now(dt.timezone.utc)

    # Determine "deadline" from tolerance
    if tolerance is None:
        deadline = None
    elif isinstance(tolerance, (int, float)):
        deadline = target + dt.timedelta(seconds=tolerance)
    elif isinstance(tolerance, str):
        deadline = _timestamp_to_utc_datetime(tolerance)
    else:
        raise ValueError(f"Unsupported type {type(tolerance)} provide for tolerance {tolerance}")

    # Raise error if currently past the "deadline"
    if deadline is None:
        pass
    elif now > deadline:
        raise ValueError(f"Current time ({now}) is past deadline "
                         + f"({deadline.isoformat()}) set by tolerance ({tolerance})")

    # Wait until timestamp
    if target > now:
        duration = (target - now).total_seconds()
        print(f"Waiting for {duration} seconds")
        time.sleep(duration)
    else:
        diff = (now - target).total_seconds()
        print(f"No wait, as target is {diff} seconds in the past")
