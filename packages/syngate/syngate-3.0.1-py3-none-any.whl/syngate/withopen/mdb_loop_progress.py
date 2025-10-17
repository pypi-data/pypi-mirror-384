'''
This module provides a single utility function `get` that returns progress 
information based on a current value and a total value. The function can return 
progress as a count (e.g., '3/10'), as a percentage (e.g., '30%'), or both 
(e.g., '3/10 - 30%'). It includes options for formatting, rounding, and 
inverting the progress percentage.

Function: get(current, total, as_percentage=True, rounded=True, decimal_places=0, 
              output_mode='both', invert_percentage=False)

Arguments:
    - current (int): The current progress value.
    - total (int): The total value representing 100% progress.
    - as_percentage (bool): If True (default), the percentage is scaled to 0–100%.
                            If False, it remains in the 0–1 decimal format.
    - rounded (bool): If True (default), the output is rounded using Python's
                      built-in round(). If False, the percentage is formatted 
                      using fixed decimal places.
    - decimal_places (int): The number of decimal places for the percentage output. 
                            Defaults to 0. Applies whether rounded is True or False.
    - output_mode (str): One of 'count', 'percentage', or 'both'. Determines the 
                         format of the return value:
                         - 'count' returns just "⟳ [current/total]"
                         - 'percentage' returns just "⟳ [xx%]"
                         - 'both' returns "⟳ [current/total - xx%]"
                         Defaults to 'both'.
    - invert_percentage (bool): If True, the function inverts the progress 
                                percentage (e.g., 90% becomes 10%) by computing 
                                (1 - current/total). Default is False.

Returns:
    - str: A formatted string representing the progress based on the chosen mode.

Behavior:
    - If total is 0, progress is treated as 0% to avoid division by zero.
    - The count portion is always formatted as "current/total".
    - If as_percentage is True, the value is multiplied by 100.
    - If rounded is True and decimal_places == 0, output uses round(value) + '%'.
    - If rounded is True and decimal_places > 0, output uses round(value, dp) + '%'.
    - If rounded is False, output uses string formatting with fixed decimal precision.
    - The return string is always wrapped in "⟳ [ ... ]" with appropriate contents 
      based on output_mode.

Example outputs:
    get(30, 100)                      → "⟳ [30/100 - 30%]"
    get(30, 100, output_mode='count') → "⟳ [30/100]"
    get(30, 100, output_mode='percentage') → "⟳ [30%]"
    get(30, 100, invert_percentage=True) → "⟳ [30/100 - 70%]"
    get(1, 4, decimal_places=2, rounded=False) → "⟳ [1/4 - 25.00%]"


def get (current, total, 
         as_percentage=True,      # True = 0-100%, False = 0-1
         rounded= True,           # Round or format
         decimal_places=0,        # Decimal precision
         output_mode='both'):     # 'count', 'percentage', or 'both'
    """
    Get progress as count, percentage, or both.

    Args:
        current (int): Current step.
        total (int): Total steps.
        as_percentage (bool): Show as 0-100 or 0-1.
        rounded (bool): Round or format output.
        decimal_places (int): Decimal places.
        output_mode (str): 'count', 'percentage', or 'both'.

    Returns:
        str: Progress string based on mode.
    """
    if total == 0:
        progress_value = 0
    else:
        progress_value = current / total

    count_str = f"{current}/{total}"

    if as_percentage:
        progress_value *= 100

    if rounded:
        if decimal_places == 0:
            progress_str = f"{round(progress_value)}%"
        else:
            progress_str = f"{round(progress_value, decimal_places)}%"
    else:
        progress_str = f"{progress_value:.{decimal_places}f}%"

    if output_mode == 'count':
        return f'⟳ [{count_str}]'
    elif output_mode == 'percentage':
        return f'⟳ [{progress_str}]'
    else:
        return f"⟳ [{count_str} - {progress_str}]"


'''



def get(current, total, 
        as_percentage=True,      # True = 0-100%, False = 0-1
        rounded=True,            # Round or format
        decimal_places=0,        # Decimal precision
        output_mode='both',      # 'count', 'percentage', or 'both'
        invert_percentage=False  # If True, invert the percentage
        ):
    """
    Get progress as count, percentage, or both.

    Args:
        current (int): Current step.
        total (int): Total steps.
        as_percentage (bool): Show as 0-100 or 0-1.
        rounded (bool): Round or format output.
        decimal_places (int): Decimal places.
        output_mode (str): 'count', 'percentage', or 'both'.
        invert_percentage (bool): If True, return the inverse percentage (e.g. 90% -> 10%).

    Returns:
        str: Progress string based on mode.
    """
    if total == 0:
        progress_value = 0
    else:
        progress_value = current / total

    if invert_percentage:
        progress_value = 1 - progress_value

    count_str = f"{current}/{total}"

    if as_percentage:
        progress_value *= 100

    if rounded:
        if decimal_places == 0:
            progress_str = f"{round(progress_value)}%"
        else:
            progress_str = f"{round(progress_value, decimal_places)}%"
    else:
        progress_str = f"{progress_value:.{decimal_places}f}%"

    if output_mode == 'count':
        return f'⟳ [ {count_str} ]'
    elif output_mode == 'percentage':
        return f'⟳ [ {progress_str} ]'
    else:
        return f'⟳ [ {count_str} - {progress_str} ]'
