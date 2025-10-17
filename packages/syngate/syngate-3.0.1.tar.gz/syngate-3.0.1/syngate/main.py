import time
import random
from datetime import datetime

import withopen as f
from . import session_id_generator


f.hide("*", display = False)
f.warning(False)


def get_current_monotonic_timestamp():
    """
    Retrieves the current monotonic timestamp.

    Returns:
        float: Current monotonic time in seconds.
    """
    return time.monotonic()


def active_event_tag(queue_name):
    """
    Writes an 'Active' tag with the current monotonic timestamp to the queue.

    Args:
        queue_name (str): The name of the queue.
    """
    now_utc = get_current_monotonic_timestamp()
    f.w(queue_name, ["Active", now_utc], is2d=False)


def done(queue_name):
    """
    Writes a 'Done' tag with the current monotonic timestamp to the queue.

    Args:
        queue_name (str): The name of the queue.
    """
    now_utc = get_current_monotonic_timestamp()
    f.w(queue_name, ["Done", now_utc], is2d=False)


def active(queue_name, pulse):
    """
    Writes an 'Active' tag with a future timestamp based on pulse duration.

    Args:
        queue_name (str): The name of the queue.
        pulse (float): Number of seconds to add to the current timestamp.
    """
    now_utc = get_current_monotonic_timestamp()
    timestamp = now_utc + pulse
    f.w(queue_name, ["Active", timestamp], is2d=False)


def ready_to_go_check(queue_id, pulse):
    """
    Checks if the queue tag is safe to proceed based on staleness or status.

    Args:
        queue_id (str): The queue identifier.
        pulse (float): The max allowable freshness duration.

    Returns:
        bool: True if safe to proceed, else False.
    """
    last_write = f.r(queue_id)
    if not last_write:
        return True

    tag_status, tag_timestamp = last_write
    now = get_current_monotonic_timestamp()
    elapsed = now - tag_timestamp

    if tag_status == "Active":
        return elapsed > pulse
    elif tag_status == "Done":
        return True
    else:
        return False


def jitter(interval=0.1, max_value=1):
    """
    Returns a random jitter value from 0 to max_value in steps of interval.

    Args:
        interval (float): Step size.
        max_value (float): Maximum jitter.

    Returns:
        int or float: Jitter value.
    """
    if interval <= 0:
        raise ValueError("interval must be > 0")
    if max_value < 0:
        raise ValueError("max_value must be >= 0")

    num_steps = int(max_value // interval)
    step = random.randint(0, num_steps)
    result = step * interval

    return int(result) if isinstance(interval, int) else round(result, 10)


def wait_until_secs_modulo(mod, tolerance=0.01):
    """
    Waits until the current time modulo `mod` is within tolerance.

    Args:
        mod (int): Modulo value in seconds.
        tolerance (float): Allowed margin of error.
    """
    while True:
        now = time.time()
        current_seconds = now % 60
        remainder = current_seconds % mod

        if remainder < tolerance or (mod - remainder) < tolerance:
            break

        time_to_next_mod = mod - remainder
        time.sleep(0.4 if time_to_next_mod > 0.5 else 0.01)


def is_first_session_id_equal(queue_id, session_id_to_check):
    """
    Checks if the first session ID in the queue matches the given one.

    Args:
        queue_id (str): The queue identifier.
        session_id_to_check (str): Session ID to verify.

    Returns:
        bool: True if it matches, else False.
    """
    last_write = f.r(queue_id)

    if isinstance(last_write, list) and last_write:
        first_session_id = last_write[0]
        return first_session_id == session_id_to_check

    return False


def get_current_time_seconds():
    """
    Returns the current time in seconds (including fractional part).

    Returns:
        float: Current second and microseconds as a float.
    """
    now = datetime.now()
    return now.second + now.microsecond / 1_000_000


def get_last_digit_of_precise_second():
    """
    Returns the last digit of the integer second with fractional microseconds.

    Returns:
        float: Last digit of the current second + fractional part.
    """
    current_time = time.time()
    fractional_seconds = current_time % 60
    seconds_int = int(fractional_seconds)
    last_digit = seconds_int % 10
    return last_digit + (fractional_seconds - seconds_int)


def enter(queue_name, pulse, wait=True, display=True):
    """
    Attempts to enter the sync gate mechanism with queuing and timing.

    Args:
        queue_name (str): Name of the queue.
        pulse (float): Max allowed freshness of 'Active' tag in seconds (positive number).
        wait (bool, optional): If False, bypasses wait logic. Defaults to True.
        display (bool, optional): If True, displays status. Defaults to True.

    Returns:
        bool: True if passed the gate, False if skipped due to wait=False.

    Raises:
        TypeError: If parameter types are incorrect.
        ValueError: If pulse is not positive.
    """

    # Type validation
    if not isinstance(queue_name, str):
        raise TypeError(f"queue_name must be a string, got {type(queue_name).__name__}")

    if not (isinstance(pulse, (int, float)) and pulse > 0):
        raise ValueError(f"pulse must be a positive number, got {pulse}")

    if not isinstance(wait, bool):
        raise TypeError(f"wait must be a bool, got {type(wait).__name__}")

    if not isinstance(display, bool):
        raise TypeError(f"display must be a bool, got {type(display).__name__}")

    # Your existing implementation goes here
    # ...

    queue_name = queue_name.strip()
    session_id = session_id_generator.get()
    queue_id = f"{queue_name}_queue"

    error_counter = 0
    fifo_counter = 6
    while True:
        try:
            holding_tag = False
    
            while True:
                seconds = get_current_time_seconds()
    
                if (0 <= seconds <= 9) or (21 <= seconds <= 29) or (41 <= seconds <= 49):
                    if ready_to_go_check(queue_name, pulse):
                        if display:
                            print(f"🧩 SYNGATE | LOADING 🟣 [{datetime.now():%H:%M:%S}]")
                        time.sleep(fifo_counter)
                        break
                    elif not wait:
                        if display:
                            print(f"🧩 SYNGATE | FLYOVER ⚫ [{datetime.now():%H:%M:%S}]")
                        return False
                else:
                    if display and not holding_tag:
                        holding_tag = True
                        print(f"🧩 SYNGATE | HOLDING 🔴 [{datetime.now():%H:%M:%S}]")
    
                time.sleep(6)
                fifo_counter -= 0.1
    
                if fifo_counter < 0:
                    possible_values = [round(x * 0.1, 1) for x in range(1, 21)]
                    fifo_counter = random.choice(possible_values)
    
            if display:
                print(f"🧩 SYNGATE | QUEUING 🟡 [{datetime.now():%H:%M:%S}]")
    
            time_secs_tag = get_last_digit_of_precise_second()
    
            if time_secs_tag > 6.5:
                possible_values = [round(x * 0.1, 1) for x in range(55, 66)]
                time_secs_tag = random.choice(possible_values)
    
            wait_until_secs_modulo(7)
            time.sleep(7 - time_secs_tag)
    
            f.w(queue_id, session_id, is2d=False)
    
            wait_until_secs_modulo(7)
    
            lucky_pick = is_first_session_id_equal(queue_id, session_id)
    
            if lucky_pick:
                if ready_to_go_check(queue_name, pulse):
                    if display:
                        print(f"🧩 SYNGATE | DEQUEUE 🟢 [{datetime.now():%H:%M:%S}]")
                    active_event_tag(queue_name)
                    return True
            elif not lucky_pick and not wait:
                if display:
                    print(f"🧩 SYNGATE | FLYOVER ⚫ [{datetime.now():%H:%M:%S}]")
                return False
    
            time.sleep(time_secs_tag)
            print("")

        except (FileNotFoundError, PermissionError) as e:
            error_counter += 1
            if error_counter > 12:
                raise  # re-raises the current exception
