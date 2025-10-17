from . import mdb_core as MDB
from . import mdb_session_id_generator as session_id_generator
from datetime import datetime, timezone
import time
import random
import uuid
import os
from . import mdb_control_file_visibility as control_file_visibility
from . import mdb_future_datetime as future_datetime
import errno # fix permission denided issue
import threading
import warnings
import ast

# Optional: Custom warning formatter to suppress filename/line info
def custom_warning_formatter(message, category, filename, lineno, file=None, line=None):
    return f"{message}\n"

warnings.formatwarning = custom_warning_formatter
    
DONE_SAFETY_DELAY = 2 #secs is is the gap when geting time dif before it trusts it
MAX_LENGTH = 100_000
STALE_PULSE_SECS = 30

def run_with_time_limit(func, timeout_seconds, *args, **kwargs):
    start_time = time.perf_counter()
    result = func(*args, **kwargs)  # blocking call
    elapsed = time.perf_counter() - start_time
    
    if elapsed > timeout_seconds:
        raise TimeoutError(f"Function exceeded timeout of {timeout_seconds} seconds (took {elapsed:.2f}s)")
    
    return result

def wait_until_secs_modulo(mod, tolerance=0.01):
    while True:
        now = time.time()
        current_seconds = now % 60
        remainder = current_seconds % mod

        if remainder < tolerance or (mod - remainder) < tolerance:
            dt = datetime.fromtimestamp(now)
            #print(f"✅ Released at: {dt.strftime('%H:%M:%S.%f')[:-3]} (second % {mod} ≈ 0)")
            break

        time_to_next_mod = mod - remainder
        if time_to_next_mod > 0.5:
            time.sleep(0.4)  # Coarse sleep
        else:
            time.sleep(0.01)  # Fine polling


def is_first_session_id_equal(folder_path, queue_file_len, session_id_to_check):
    """
    Returns True if the first session ID in the queue matches session_id_to_check.
    Otherwise, returns False.
    """
    last_write = read_majority_vote(queue_file_len, folder_path)
    
    if isinstance(last_write, list) and last_write:
        first_session_id = last_write[0][0]  # Assuming session_id is the first element in tuple/list
        return first_session_id == session_id_to_check
    else:
        # Queue is empty or invalid
        return False


def read_majority_vote(queue_name_id, folder_path):
    """
    Reads the file data based on majority vote logic to avoid corruption.
    Retries up to 9 times if the file is in use (detected via ValueError).

    Args:
        queue_name_id (str): Identifier for the queue file.
        folder_path (str): Directory containing the queue files.

    Returns:
        list or None: Contents of the file as determined by majority voting.

    Raises:
        ValueError: If the file is in use (ValueError) for all 9 attempts.
        Exception: Any other unexpected exception is raised immediately.
    """
    for attempt in range(9):
        try:
            data = MDB.majority_vote_file_reader(queue_name_id, folder_path, single_read  = True)
            if data is not None:
                return data
        except ValueError:
            # File is in use, retry
            continue
        except Exception as e:
            # Any other error, raise it immediately
            raise e  # correct


def jitter(interval = 0.1, max_value = 1):
    """
    Returns a random value in [0, max_value], in steps of `interval`.
    - If interval is an int, returns int values.
    - If interval is a float, returns float values (rounded to avoid float drift).
    """
    if interval <= 0:
        raise ValueError("interval must be > 0")
    if max_value < 0:
        raise ValueError("max_value must be >= 0")
    
    num_steps = int(max_value // interval)  # number of valid steps
    step = random.randint(0, num_steps)     # choose a random step
    result = step * interval

    # Return int if interval is int
    if isinstance(interval, int):
        return int(result)
    else:
        return round(result, 10)  # avoid float precision issues


def add_to_queue_len(folder_path, queue_file_len, session_id):
    max_retries = 12
    retry_delay = 1

    now_utc = get_current_monotonic_timestamp()
    data_to_write = [[session_id, now_utc]]

    for attempt in range(max_retries):
        try:
            MDB.write_all_files(data_to_write, folder_path, queue_file_len, single_write=True, hide=True)
            break  # Success, exit retry loop
        except OSError as e:
            if e.errno == errno.EACCES:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)  # Wait and retry
                    continue
                else:
                    raise
            else:
                raise

def ready_to_go_check(folder_path, queue_id):
    """
    Checks if it's safe for the current process to proceed based on the tag file.

    Returns:
        bool: True if queue is free, stale, or safe; False if still actively held.
    """
    try:
        last_write = read_majority_vote(queue_id, folder_path)
        
        if not last_write or not isinstance(last_write, list) or len(last_write) != 3:
            #print("🆕 Tag is missing or malformed. Assuming free but adding jitter.")
            return True

        _, tag_timestamp, tag_status = last_write
        now = time.monotonic()
        elapsed = now - tag_timestamp

        if tag_status == "Active":
            if elapsed > STALE_PULSE_SECS:
                #print("🟢 Active tag is stale. Proceeding.")
                return True
            else:
                #print("🔴 Active tag is still fresh. Waiting.")
                return False

        elif tag_status == "Done":
            if elapsed >= DONE_SAFETY_DELAY:
                #print("✅ Done tag is aged enough. Proceeding.")
                return True
            else:
                #print("⚠️ Done tag is too fresh. Backing off with jitter.")
                return False
        else:
            #print(f"❓ Unknown tag status: {tag_status}. Blocking by default.")
            return False

    except Exception as e:
        #print(f"❗ Exception in ready_to_go_check(): {e}")
        return False


def event_tag(folder_path, queue_id, session_id=None):

    full_path = os.path.join(folder_path, queue_id)
    now_utc = get_current_monotonic_timestamp()
    try:
        if os.path.exists(full_path):
            last_write = read_majority_vote(queue_id, folder_path)
            last_write[1] = now_utc
            if session_id:
                last_write[0] = session_id
                last_write[2] = "Active"
            else:
                last_write[2] = "Done"    
            MDB.write_all_files(last_write, folder_path, queue_id, single_write = True, hide=True)
        else:
            session_id = 'new'
            last_user_timestamp = [session_id, now_utc, "Done"]
            MDB.write_all_files(last_user_timestamp, folder_path, queue_id, single_write = True, hide=True)      
    except ValueError:
        session_id = '1111'
        now_utc = get_current_monotonic_timestamp()
        last_user_timestamp = [session_id, now_utc, "Active"]
        MDB.write_all_files(last_user_timestamp, folder_path, queue_id, single_write = True, hide=True)
    except OSError as e:
        if e.errno == errno.EACCES:
            return False
        else:
            raise 

    return True 

def end_queue_len_event(folder_path, queue_file_len, entry_len_of_queue):
    """
    Finalizes the queue event by marking remaining sessions as completed.

    Args:
        folder_path (str): Path where queue files are stored.
        queue_file_len (str): Identifier for the queue length file.
        entry_len_of_queue (int): Total number of processes/console instances in the queue.

    Returns:
        bool: True if successful, False if a permission error prevented writing.
    """
    queue_full_list = read_majority_vote(queue_file_len, folder_path)
    if not queue_full_list:
        current_queue_len = 0
        active_queue_len = []
    else:
        current_queue_len  = len(queue_full_list)
        left_in_the_queue = entry_len_of_queue - current_queue_len
        active_queue_len = queue_full_list[entry_len_of_queue:]
    try:
        MDB.write_all_files(active_queue_len, folder_path, queue_file_len, hide=True)  
    except OSError as e:
        if e.errno == errno.EACCES:
            return False
        else:
            raise  # re-raise any unexpected OSError
    finally:
        pass       
    return True


def get_current_monotonic_timestamp():
    """
    Retrieves the current monotonic timestamp.

    Returns:
        float: Current monotonic time in seconds.
    """
    return time.monotonic()

def seconds_to_next_minute():
    """Returns the number of seconds until the next full minute."""
    import time
    current_time = time.time()
    seconds = 60 - (current_time % 60)
    return seconds

def alert_warning():
    # get whether to alert  for mew file/warning file not in consoles mode.
    whether_to_alert_file = "__hide_new_alert_987812919120.txt"
    control_file_visibility.unhide_folder(whether_to_alert_file)
    try:
        with open(whether_to_alert_file, "r") as file:
            content = file.read().strip()
            whether_to_alert = ast.literal_eval(content)
    except FileNotFoundError:
        with open(whether_to_alert_file, "w") as file:
            file.write(str((True)))  # Writes them as a tuple string, e.g., "(True, False)"
            whether_to_alert = True
    control_file_visibility. hide_folder(whether_to_alert_file)

    return whether_to_alert
            
        #---

def wait_read(folder_path, queue_name, skip_memory_val = False):
    """
    Manages the queue system, waits for the process's turn, and reads validated file content.

    Args:
        queue_name (str): The name of the queue (logical resource identifier).
        wait (bool, optional): If True, the process will wait until it is safe to read. Defaults to False.
        debug (bool, optional): Enables debug mode for logging internal steps. Defaults to False.

    Returns:
        list: Final consistent read data from the file after obtaining access.
    
    Raises:
        Exception: If repeated errors occur during file reading (e.g., permission errors).
    """
    
    queue_name = queue_name.strip()
    session_id = session_id_generator.get()

    queue_id = f"{queue_name}_queue"
    queue_file_len = f"{queue_name}_queue_len"

    consoles_path  = f"{queue_name}_consoles"
    consoles_info = read_majority_vote(consoles_path, folder_path)

    try:
        consoles = consoles_info[0]
        display = consoles_info[1]
    except TypeError:
        
        consoles = False
        display = False

        if  alert_warning():
            print("🛡️ [NEW] Multiple C. OFF → f.consoles(txt_name, multiple=True, alert=True/False) | Hide alert: f.warning(False).")
            
        MDB.write_all_files([consoles, display] , folder_path, consoles_path, hide = True, single_write = True) #peform write  

    if consoles:
        counter = 0
        while True:

            if counter <= 1:
                if display and counter == 0:
                    entered_tag = f"\n🛡️ QUEUING 🟣 [{datetime.now():%H:%M:%S}]"
                    print(entered_tag)
            
            wait_until_secs_modulo(30)
            
            time.sleep(jitter(0.3, 25.5))
            
            add_to_queue_len(folder_path, queue_file_len, session_id)
    
            wait_until_secs_modulo(30)
    
            time.sleep(jitter(0.2, 3))
               
            if is_first_session_id_equal(folder_path, queue_file_len, session_id):
                if ready_to_go_check(folder_path, queue_id):
                    if display:
                        pass_tag = f"🛡️ DEQUEUE 🟢 [{datetime.now().strftime('%H:%M:%S')}]\n"
                        print(pass_tag)
                    break       

            next_retry_sec = seconds_to_next_minute() + (counter * 60)

            if display: 
                print(f"🛡️ QUEUE MISSED 🟡 Try again in {next_retry_sec/60:.2f} minutes... [{future_datetime.get(next_retry_sec)}]")
            time.sleep(next_retry_sec) 
            counter += 1

    else:
        false_proceed = False

    #---
    false_proceed = False
    #---
     # session id means active - without session id means done
    if event_tag(folder_path, queue_id, session_id = session_id) is False:
        false_proceed = True     
    #---
        
    if false_proceed == False:
        
        expected_uncorrupted_data = run_with_time_limit(read_majority_vote, 15, queue_name, folder_path)

        if skip_memory_val is False:
            if expected_uncorrupted_data and len(expected_uncorrupted_data) >= MAX_LENGTH:
                raise MemoryError(f"Memory full: maximum allowed length is {MAX_LENGTH:,} rows. Please delete/ Trim to free up space.")
        return expected_uncorrupted_data
