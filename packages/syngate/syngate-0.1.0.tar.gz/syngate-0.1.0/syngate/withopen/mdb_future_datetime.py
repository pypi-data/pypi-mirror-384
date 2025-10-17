#import future_datetime 

#future_datetime.get(value, unit='h', datetime_format=False, format_12h=True)

'''
Module: Time Delta Calculator

Description:
    This module provides a utility function to add a time delta to the current 
    datetime and return the resulting future time as a formatted string. The 
    function allows customization of the unit of time being added, the format 
    of the returned datetime string (either in 12-hour or 24-hour format), and 
    whether a full datetime string is returned or just the time portion.

    The supported units of time include:
    - Seconds ('s')
    - Minutes ('m')
    - Hours ('h')
    - Days ('d')
    - Months ('mo') - approximated as 30 days per month
    - Years ('y') - approximated as 365 days per year

Use Case Scenarios:
    1. **Time Tracking & Scheduling:**
        - If you need to determine a time in the future (e.g., 5 hours from now), 
          this function can be used to get the exact time in either 12-hour or 
          24-hour format.
    2. **Event Scheduling & Reminders:**
        - Schedule events or reminders, adding days, months, or years, and 
          formatting the result in a way that suits the need of the user interface.
    3. **Date Manipulation for Reports:**
        - Generate reports with relative time manipulations (e.g., 2 months ahead) 
          and easily format the output for readability.
    4. **Automated Time-based Actions:**
        - Automate actions that require time deltas, such as setting expiry times 
          (e.g., 30 minutes from now) in APIs or scheduling jobs.

How to Use:
    Call the function `get()` with the following parameters:

    Parameters:
    - `value` (int): The amount of time you want to add.
        - This is the value of the time delta. For example, if you want to add 3 hours, `value` would be `3`.
    - `unit` (str): The unit of time for the delta.
        - Supported units are:
            - 's' for seconds
            - 'm' for minutes
            - 'h' for hours
            - 'd' for days
            - 'mo' for months (approximated as 30 days)
            - 'y' for years (approximated as 365 days)
    - `datetime_format` (bool, optional): Whether to return the full datetime (including date).
        - If `True`, the function returns the complete datetime in the form `YYYY-MM-DD HH:MM:SS AM/PM` (12-hour format) or `YYYY-MM-DD HH:MM:SS` (24-hour format).
        - If `False`, it only returns the time portion (e.g., `HH:MM:SS`).
        - Default: `False`
    - `format_12h` (bool, optional): Whether to use 12-hour format with AM/PM.
        - If `True`, the function returns the time in 12-hour format with AM/PM.
        - If `False`, it returns the time in 24-hour format.
        - Default: `True`

    Example Usage:
    1. **Adding 5 hours and displaying full datetime in 12-hour format:**
        ```python
        get(5, 'h', datetime_format=True, format_12h=True)
        ```
        Output (example): `2025-05-19 10:15:00 PM`

    2. **Adding 2 days and displaying just the time portion in 24-hour format:**
        ```python
        get(2, 'd', datetime_format=False, format_12h=False)
        ```
        Output (example): `12:15:00`

    3. **Adding 3 months and displaying full datetime in 24-hour format:**
        ```python
        get(3, 'mo', datetime_format=True, format_12h=False)
        ```
        Output (example): `2025-08-19 23:45:00`

    4. **Adding 1 year and displaying full datetime in 12-hour format:**
        ```python
        get(1, 'y', datetime_format=True, format_12h=True)
        ```
        Output (example): `2026-05-19 09:30:00 AM`

'''

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def get(value, unit='s', datetime_format=False, format_12h=True):
    """
    Add a time delta to the current datetime and return a formatted string.

    Args:
        value (int): Amount of time to add.
        unit (str, optional): Unit of time ('s', 'm', 'h', 'd', 'mo', 'y'). Defaults to 'h'.
        datetime_format (bool): If True, always return full datetime format.
        format_12h (bool): If True, use 12-hour format with AM/PM. If False, use 24-hour format.

    Returns:
        str: Formatted future time string.
    """
    now = datetime.now()
    unit = unit.lower()

    if unit == 's':
        future = now + timedelta(seconds=value)
        delta = timedelta(seconds=value)
    elif unit == 'm':
        future = now + timedelta(minutes=value)
        delta = timedelta(minutes=value)
    elif unit == 'h':
        future = now + timedelta(hours=value)
        delta = timedelta(hours=value)
    elif unit == 'd':
        future = now + timedelta(days=value)
        delta = timedelta(days=value)
    elif unit == 'mo':
        future = now + relativedelta(months=value)
        delta = timedelta(days=30 * value)  # Approximate month
    elif unit == 'y':
        future = now + relativedelta(years=value)
        delta = timedelta(days=365 * value)  # Approximate year
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    # Format selection
    if datetime_format or delta >= timedelta(days=1):
        fmt = '%Y-%m-%d %I:%M:%S %p' if format_12h else '%Y-%m-%d %H:%M:%S'
    else:
        fmt = '%I:%M:%S %p' if format_12h else '%H:%M:%S'

    return future.strftime(fmt)
