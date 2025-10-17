#import jupyter_max.days_ago as days_ago
#days_ago.get (past_time, short=False, words=False,fractional=False)


"""
Human-Readable Time Difference Utilities
========================================

Provides utility functions for generating human-readable relative time strings
based on datetime input. Useful for logs, interfaces, reports, or any output
where readable durations or time differences are needed.

Functions:
----------

1. get(past_time, short=False, words=False, fractional=False)

   Description:
   ------------
   Returns a human-readable string representing the time difference between a given 
   datetime value and the current moment. Supports both past and future times, 
   with flexible formatting options.

   When to use:
   ------------
   - To display relative time differences in user interfaces, logs, or reports.
   - To show durations like "5 mins ago", "in 2 days time", or "just now".
   - When you want to choose between detailed breakdowns or combined fractional time units.

   Parameters:
   -----------
   - past_time: datetime
       A datetime object to compare against the current time.
   - short: bool (default: False)
       If True, use compact unit abbreviations (e.g., "2d 3h").
   - words: bool (default: False)
       If True, use full unit names with proper pluralization (e.g., "2 days").
   - fractional: bool (default: False)
       If True, combine smaller units into decimal fractions 
       (e.g., "1.5 hours" instead of "1 hour, 30 mins").

   Examples:
   ---------
   >>> get(datetime.now() - timedelta(minutes=5), short=True)
   '5m ago'

   >>> get(datetime.now() + timedelta(days=2, hours=4))
   'in 2 days, 4 hours time'

   >>> get(datetime.now() - timedelta(hours=1, minutes=30), fractional=True)
   '1.5 hours ago'


2. get_range(start_time, end_time, short=True, words=False, fractional=False)

   Description:
   ------------
   Returns a human-readable string describing the time range between two datetime values.
   If both datetimes fall within the same minute, returns a single time string using `get()`.

   When to use:
   ------------
   - To display a duration between two future or two past times.
   - To show time spans like "2 mins - 4 mins ago" or "in 1 day - 2 days time".

   Parameters:
   -----------
   - start_time: datetime
       The earlier datetime in the range.
   - end_time: datetime
       The later datetime in the range.
   - short: bool (default: True)
       If True, use compact unit abbreviations (e.g., "2d 3h").
   - words: bool (default: False)
       If True, use full unit names with pluralization.
   - fractional: bool (default: False)
       If True, express durations as decimal fractions.

   Constraints:
   ------------
   - start_time must be earlier than or equal to end_time.
   - Both times must be either in the past or both in the future relative to now.

   Examples:
   ---------
   >>> get_range(datetime.now() - timedelta(minutes=5), datetime.now() - timedelta(minutes=3))
   '5 mins - 3 mins ago'

   >>> get_range(datetime.now() + timedelta(minutes=2), datetime.now() + timedelta(minutes=4))
   'in 2 mins - 4 mins time'

   >>> get_range(datetime.now() + timedelta(minutes=2), datetime.now() + timedelta(minutes=2, seconds=30))
   'in 2 mins time'
"""


from datetime import datetime, timedelta
from dateutil.parser import parse

def get(past_time, short= True , words=False, fractional=False):
    """
    Return human-readable relative time between `past_time` and now.

    Parameters:
    - past_time: datetime or string (various formats accepted)
    - short: bool (compact abbreviations, e.g. "2d 3h")
    - words: bool (pluralize units properly, e.g. "2 days")
    - fractional: bool (combine smaller units as decimal fractions,
                   e.g. "1.5 hours" instead of "1 hour, 30 mins")

    Returns a string like:
    - "just now"
    - "5 mins ago"
    - "1.5 hours ago" (if fractional=True)
    - "2 days ago"
    - "in 3 hours time"
    """

    def plural(unit, value):
        if words:
            return f"{value} {unit}" + ("" if value == 1 else "s")
        else:
            if short:
                return f"{value}{unit[0]}"
            else:
                return f"{value} {unit}"

    if isinstance(past_time, str):
        try:
            past_time = parse(past_time)
        except Exception as e:
            raise ValueError(f"Invalid date string format: {past_time}") from e

    if not isinstance(past_time, datetime):
        raise TypeError("Input must be a datetime object or a valid string")

    now = datetime.now()
    diff = past_time - now
    seconds = diff.total_seconds()
    is_future = seconds > 0
    seconds = abs(seconds)

    if seconds < 5:
        return "just now"

    days = int(seconds // 86400)
    remainder = seconds % 86400
    hours = int(remainder // 3600)
    remainder %= 3600
    minutes = int(remainder // 60)
    secs = int(remainder % 60)

    if fractional:
        if days >= 1:
            # Combine days + fractional day from hours and minutes
            fractional_day = (hours * 3600 + minutes * 60 + secs) / 86400
            total_days = round(days + fractional_day, 1)
            unit_str = "day" if total_days == 1 else "days"
            result = f"{total_days} {unit_str}" if words else f"{total_days}d"
        else:
            # Combine hours + fractional hour from minutes and seconds
            fractional_hour = (minutes * 60 + secs) / 3600
            total_hours = round(hours + fractional_hour, 1)
            unit_str = "hour" if total_hours == 1 else "hours"
            result = f"{total_hours} {unit_str}" if words else f"{total_hours}h"
    else:
        parts = []
        if days > 0:
            parts.append(plural("day", days))
        if hours > 0:
            parts.append(plural("hour", hours))
        if minutes > 0:
            parts.append(plural("min", minutes))
        if not parts and secs > 0:
            parts.append(plural("sec", secs))
        result = ", ".join(parts) if not short else " ".join(parts)

    return f"in {result} time" if is_future else f"{result} ago"




def get_range(start_time, end_time, short=True, words=False, fractional=False):
    """
    Return a human-readable relative time range between two datetimes or date strings.

    If start_time and end_time are the same (to the minute), return `get(start_time)`.

    - Both must be either in the past or in the future relative to now.
    - Raises ValueError if the range crosses 'now'.
    """

    # Parse inputs if strings
    if isinstance(start_time, str):
        try:
            start_time = parse(start_time)
        except Exception as e:
            raise ValueError(f"Invalid start_time string format: {start_time}") from e

    if isinstance(end_time, str):
        try:
            end_time = parse(end_time)
        except Exception as e:
            raise ValueError(f"Invalid end_time string format: {end_time}") from e

    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        raise TypeError("Inputs must be datetime objects or valid date strings")

    # Auto-sort: Ensure start_time <= end_time
    if start_time > end_time:
        start_time, end_time = end_time, start_time

    # Normalize to the minute and drop tzinfo
    def normalize_to_minute(dt):
        if dt.tzinfo:
            dt = dt.astimezone(tz=None)
        return dt.replace(tzinfo=None, second=0, microsecond=0)

    norm_start = normalize_to_minute(start_time)
    norm_end = normalize_to_minute(end_time)

    if norm_start == norm_end:
        return get(start_time, short=short, words=words, fractional=fractional)

    now = datetime.now()
    start_delta = (start_time - now).total_seconds()
    end_delta = (end_time - now).total_seconds()

    def trim(s):
        return s.replace(" ago", "").replace("in ", "").replace(" time", "")

    if start_delta > 0 and end_delta > 0:
        s1 = trim(get(start_time, short=short, words=words, fractional=fractional))
        s2 = trim(get(end_time, short=short, words=words, fractional=fractional))
        return f"in {s1} - {s2} time"

    elif start_delta < 0 and end_delta < 0:
        s1 = trim(get(start_time, short=short, words=words, fractional=fractional))
        s2 = trim(get(end_time, short=short, words=words, fractional=fractional))
        return f"{s1} - {s2} ago"

    else:
        raise ValueError("Both times must be either in the past or in the future (no crossing now)")
