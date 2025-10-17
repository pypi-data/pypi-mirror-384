def add_to_queue_len(folder_path, queue_file_len, session_id):
    max_retries = 9
    retry_delay = 1  # seconds
    WRITE_WAIT_WINDOW = 2  # seconds

    try:
        for attempt in range(max_retries):
            toggle_folder_visibility(folder_path, queue_file_len, show=True)

            proceed_counter = 0
            jitter_delay()

            while proceed_counter <= NUMERO_ACCESS_GRANTED_CONFIRMATION:
                last_write = read_majority_vote(queue_file_len, folder_path)

                if last_write and isinstance(last_write, list) and len(last_write) > 0:
                    last_record = last_write[-1]  # Get the latest entry
                    if isinstance(last_record, list) and len(last_record) == 2:
                        last_write_time = last_record[1]
                        now = datetime.now(timezone.utc).timestamp()
                        elapsed = now - last_write_time

                        print(f"Elapsed since last write: {elapsed:.2f} seconds")

                        if elapsed < WRITE_WAIT_WINDOW:
                            proceed_counter = 0
                            time.sleep(3)
                        else:
                            proceed_counter += 1
                    else:
                        # Malformed record, ignore and proceed
                        proceed_counter += 1
                else:
                    proceed_counter += 1

            # Ready to write to the queue
            if not last_write:
                last_write = []

            now_utc = get_current_utc_timestamp()
            last_write.append([session_id, now_utc])

            try:
                MDB.write_all_files(last_write, folder_path, queue_file_len)
                break  # Success
            except OSError as e:
                if e.errno == errno.EACCES:  # Permission denied
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return False
                else:
                    raise  # Unexpected error

    finally:
        toggle_folder_visibility(folder_path, queue_file_len, show=False)

    return len(last_write)


    counter = 1
    consoles = 1  # ⬅️ Change this to scale (e.g., 5 for original behavior)
    
    # Scalable constants based on 5-console origin
    modulo_secs = int(6 * consoles)
    
    jitter1_min = 0.06 * consoles      # Was 0.3
    jitter1_max = 5.1 * consoles       # Was 25.5
    
    jitter2_min = 0.04 * consoles      # Was 0.2
    jitter2_max = 0.6 * consoles       # Was 3.0
    
    while True:
        wait_until_secs_modulo(modulo_secs)
    
        time.sleep(jitter(jitter1_min, jitter1_max))
    
        add_to_queue_len(folder_path, queue_file_len, session_id)
    
        wait_until_secs_modulo(modulo_secs)
    
        time.sleep(jitter(jitter2_min, jitter2_max))
    
        if is_first_session_id_equal(folder_path, queue_file_len, session_id):
            if ready_to_go_check(folder_path, queue_id):
                break
    
        # Retry sleep: scaled retry + scaled seconds_to_next_minute()
        retry_delay = scaled_seconds_to_next_minute(consoles) + (12 * consoles * counter)
        time.sleep(retry_delay)
    
        counter += 1
        if counter >= consoles:
            counter += 1  # Preserved from original behavior



"""
def consoles(multiple, display):
    
    if not isinstance(multiple, bool):
        raise ValueError("The 'multiple' argument must be either True or False.")
    if not isinstance(display, bool):
        raise ValueError("The 'display' argument must be either True or False.")
        
    console_mode_file = "__console_987812919120.txt"
    control_file_visibility. unhide_folder(console_mode_file)
    with open(console_mode_file, "w") as file:
        file.write(str((multiple, display)))  # Writes them as a tuple string, e.g., "(True, False)"
    control_file_visibility. hide_folder(console_mode_file)
"""


# Optional: Custom warning formatter to suppress filename/line info
def custom_warning_formatter(message, category, filename, lineno, file=None, line=None):
    return f"{message}\n"

warnings.formatwarning = custom_warning_formatter

def warn_if_slow(start_time: float) -> None:
    """
    Calculates elapsed time from `start_time` and issues a warning
    if it exceeds the allowed threshold.

    Args:
        start_time (float): The starting time (from time.perf_counter()).

    Returns:
        None
    """
    elapsed = time.perf_counter() - start_time
    limit = set_file_limit_in_secs()[0]

    if elapsed >= limit:
        warnings.warn(
            f"\n🛡️CleanDB | ⚠️ CONSIDER REDUCING FILE SIZE OR LIMIT MULTIPLE CONSOLE USAGE FOR SPEED"
            f" | RunTime => { elapsed:.2f} secs (Limit: {limit:.2f} secs).\n\n"
            f"                                          🗝️ Read documentation to increase timeout.\n"
        )
