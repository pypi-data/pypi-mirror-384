from . import mdb_core as core
from . import mdb_validations as validations
from . import mdb_wait_queue as wait_queue
import os
from . import mdb_date_change as date_change
from datetime import datetime
from . import mdb_others as others 
from . import mdb_mini_guide as mini_guide 
from . import mdb_control_file_visibility as control_file_visibility
import warnings
import time
from . import mdb_how_long as how_long


def write(txt_name: str, write_list: list , is2d = None) -> None:
    """
    Writes a list of data to the main file and its backups after validating structure.
    To reset (clear) the file, pass an empty list `[]` as `write_list`.
    This is useful when you want to wipe data clean or intentionally restart
    due to a structure mismatch.

    This function:
        - Normalizes the file name and ensures the target folder exists.
        - Validates that the new `write_list` matches the structure of the existing file (if any).
        - Serializes and writes the data to all backup versions of the file.

    Args:
        txt_name (str): Base name of the file to write to.
        write_list (list): List of rows to write. Must match structure of existing file if not empty.

    Raises:
        ValueError:
            - If `write_list` is non-empty and its row structure doesn't match the current file.
            - Example: writing a 2D list when the file is 1D, or inconsistent row lengths.

    Returns:
        None
    """

    if is2d not in (None, True, False):
        raise TypeError("Parameter 'is2d' must be either None, True, or False.")

    write_list= validations.normalize_to_list(write_list)        
    folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name, skip_validation_error = True)
    
    if validation:
        write_list = validations.normailize_to_2d (write_list , is2d) 

    write_list = core.validate_and_register_row_shape(folder_path, write_list, validation, validation_path, is2d) 
    
    wait_queue.wait_read(folder_path, txt_name) # Not needed - for help to know when a file is active.

    if not write_list:
        core.write_all_files('', folder_path, validation_path, hide = True) # validation name
        write_list = ''

    core.write_all_files(write_list, folder_path, txt_name) #peform write  
  
    queue_id = f"{txt_name}_queue"
    wait_queue.event_tag(folder_path, queue_id)
    
    others.hide_hidden_files()


def w(txt_name, write_list, is2d=None):
    """
    Times the execution of the 'write' function and issues a warning if it exceeds allowed duration.
    """
    write(txt_name, write_list, is2d)  # Perform the write


def read(txt_name: str, index: list | None = None, set_new: list | None = [], notify_new: bool = True) -> list | None:
    """
    Reads a file and returns its content, or returns `set_new` if the file is missing.

    Args:
        txt_name (str): The base name of the file.
        set_new (list | None): Must be either [] or None. Used when the file doesn't exist.
        notify_new (bool): If True, triggers an action or message when a new file is detected.

    Returns:
        list | None: The file content if it exists, or `set_new` if not.

    Raises:
        ValueError:
            - If set_new is not [] or None.
            - If notify_new is not a boolean.
    """

    # Validate `set_new`
    if set_new not in ([], None):
        raise ValueError("Invalid value for set_new. Only [] or None are allowed.")
    
    # Validate `notify_new`
    if not isinstance(notify_new, bool):
        raise ValueError("Invalid value for notify_new. Only True or False are allowed.")

    # Validate index type
    if not (index is None or isinstance(index, (int, list, tuple))):
        raise TypeError("Index must be an int, list, tuple, or None.")

    folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name)
    proposed_uncorrupted_data = wait_queue.wait_read(folder_path, txt_name, skip_memory_val = True) 
    if proposed_uncorrupted_data is None:  # New file
        core.delete_empty_folder(folder_path) # folder was already created , so delete.
        if notify_new:
            if not os.path.isdir(os.path.dirname(validation_path)):
                print(f"🔔 New file detected > [ {txt_name} ] <")
        return set_new

    core.validate_and_register_row_shape(folder_path, proposed_uncorrupted_data, validation, validation_path) 

    queue_id = f"{txt_name}_queue"
    wait_queue.event_tag(folder_path, queue_id)

    others.hide_hidden_files()


    if index is not None:
        return others.smart_select(proposed_uncorrupted_data, index) #select function using specified index/indexes
    
    return proposed_uncorrupted_data # not proposed anymore but now validated


def r(txt_name: str, index=None, set_new= [], notify_new= False):
    """
    Times the execution of the 'read' function and issues a warning if it exceeds allowed duration.
    Delegates actual reading to `read()`.
    """
    result = read(txt_name, index=index, set_new=set_new, notify_new=notify_new)
    return result


def append_plus (txt_name: str, append_list: list , is2d = None) -> list:
    """
    Appends new data to existing validated content and writes the combined result to multiple backup files.
    
    This function performs the following steps:
    1. Resolves paths and retrieves the validation schema for the specified text file.
    2. Validates the structure of the new data (`append_list`) against the schema.
    3. Reads the most reliable existing version of the text file using a majority vote mechanism.
    4. Combines (`+`) the existing content with the new data.
    5. Writes the merged content to all backup files, overwriting them.
    
    Parameters:
    -----------
    txt_name : str
        The name of the target text file (used to resolve paths and validation schema).
        
    append_list : list
        A list of new data rows to append. Each row must match the expected structure.
    
    Returns:
    --------
    list
        The full list of data rows after appending (i.e., existing + new).
    
    """

    if is2d not in (None, True, False):
        raise TypeError("Parameter 'is2d' must be either None, True, or False.")

    append_list = validations.normalize_to_list(append_list)
    folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name)

    if validation:
        write_list = validations.normailize_to_2d (append_list , is2d) 

    append_list = core.validate_and_register_row_shape(folder_path, append_list, validation , validation_path, list2d=is2d)
    proposed_uncorrupted_data =  wait_queue.wait_read(folder_path, txt_name)
    if proposed_uncorrupted_data is None:
        proposed_uncorrupted_data = []
        
    write_list = list(proposed_uncorrupted_data) + list(append_list)
    core.write_all_files(write_list, folder_path, txt_name) #peform write  

    queue_id = f"{txt_name}_queue"
    wait_queue.event_tag(folder_path, queue_id)
    
    others.hide_hidden_files()

    return write_list

def a(txt_name, append_list, is2d=None, timeout = None):
    """
    Times the execution of the 'append_plus' function and issues a warning if it exceeds allowed duration.
    Delegates actual appending to `append_plus()`.
    """
    result = append_plus(txt_name, append_list, is2d)
    return result

def _delete(
    txt_name: str,
    del_list: list = [],
    index: int = None,
    cutoff: int = None,
    keep: int = None,
    reverse: bool = False,
    size: int = None
) -> int | list:
    """
    Deletes matching entries from a file based on a delete list.

    Supports deletion using value match, cutoff limits, or keep limits.
    
    It's important to note that the author didn't use Pandas or any other libraries here,
    in order to avoid maintenance issues and dependencies.

    Args:
        txt_name (str): File to delete from.
        del_list (list): Items to delete.
        is_2d (bool): Whether data is 2D.
        index (int | None): Index for comparison in 2D rows.
        cutoff (int | None): Max number of deletions per value.
        keep (int | None): How many entries to retain per value.
        reverse (bool): If True, processes the list in reverse order.
        size (int | None): Trims the list to this length after deletion.

    Returns:
        int: Number of items deleted.

    Raises:
        IndexError: If index is missing for 2D or invalid for 1D.
        TypeError, ValueError: For invalid arguments.
    """
    
    # Continue with rest of the logic
    delete_counter = 0
    del_list= validations.normalize_to_list(del_list)
    index, del_list = validations.validate_delete_parameters_and_return_index(del_list, cutoff, keep, size, index, reverse)

    # uf the file doesnt exist yet
    if txt_name not in listdir(display = False):
        raise FileNotFoundError(f"The file '{txt_name}' does not exist in yet! .")
            
    folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name)
    file = proposed_uncorrupted_data =  wait_queue.wait_read(folder_path, txt_name, skip_memory_val = True)
    if  proposed_uncorrupted_data  is None:
         proposed_uncorrupted_data  = []

    # Concatenate items in sublists, leave strings as-is, convert others to string
    # Concatenate important for mutiple index deletion
    str_del_list = [
        elem if isinstance(elem, str)
        else ''.join(str(i) for i in elem) if hasattr(elem, '__iter__') else str(elem)
        for elem in del_list
    ]
    
    # Deletion rules filter is to get the number of times an item will be delete.
    if cutoff:
        deletion_rules_filter = str_del_list * cutoff
    elif keep:
        deletion_rules_filter = core.get_keep_deletion_rules_filter(file, index, str_del_list, keep)
    else:
        deletion_rules_filter = str_del_list

    no_del_list = True #means no delete list, skip to check len_size
    if del_list:
        no_del_list = False
    
        # Reverse is a ascending and descending function.
        if reverse:
            file.reverse()
            
        # if a 1D list it helps the next step to indentify it is a 1D list. index not required.
        
        if not validation:
            raise ValueError("❗Validation missing. Perform create a write or append function before proceeding.")

        elif validation == '1D':
            is_2D = True
            if index != None:
                raise IndexError("Index parameter for a Normal list should be None | index = None.") 
        elif isinstance(int(validation), int):
            is_2D = False
            if index == None:
                raise IndexError("Index parameter is required when processing a 2D list.")
        else:
            raise RuntimeError("❗ Failed to get validation tag... retry again")
            
        # items not deleted, get mumber of deletions. 
        remainingItems, delete_counter = core.delete_heart(file, deletion_rules_filter, index, is_2D, cutoff, keep)  
    
        if reverse: #if reversed intially, a reversal is important for output.   
            remainingItems.reverse()   

    #------------------------------------------------------------------------------------------------------------------
    if size:
        if not no_del_list:
            remainingItems = remainingItems[-size:] 
        else:
            original_len = len(file)
            if size is not None:
                remainingItems = file[-size:]
            new_len = len(remainingItems)
            delete_counter = original_len - new_len
    #-----------------------------------------------------------------------------------------------------------------
            
    core.write_all_files(remainingItems, folder_path, txt_name) #peform write 
    
    queue_id = f"{txt_name}_queue"
    wait_queue.event_tag(folder_path, queue_id)
    
    others.hide_hidden_files()

    return delete_counter, remainingItems

def d(txt_name, del_list=[], index=None, cutoff=None, keep=None, reverse=False, size=None):
    """
    Times the execution of the '_delete' function and issues a warning if it exceeds allowed duration.
    Delegates actual deletion to `_delete()`.
    """
    result = _delete(
        txt_name=txt_name,
        del_list=del_list,
        index=index,
        cutoff=cutoff,
        keep=keep,
        reverse=reverse,
        size=size
    )
    return result
    

def backup(txt_name, display=True):
    """
    Creates a backup of the specified file or all files, depending on the input.

    If `txt_name` is '*', the function backs up all files by calling 
    `core.select_star_copy_paste_folder()`. Otherwise, it backs up the specified 
    file using `core.cope_and_paste_file()` into the "Backup 💾" folder.

    Parameters:
        txt_name (str): The name of the text file to back up, or '*' to back up all files.
        display (bool, optional): Whether to display progress or status messages during 
            the backup operation. Defaults to True.

    Raises:
        ValueError: If `display` is not a boolean value.

    """
    if not isinstance(display, bool):
        raise ValueError("Parameter 'display' must be either True or False.")
    if txt_name == "*":
        core.select_star_copy_paste_folder(display,"Backups",None)
    else:
        core.cope_and_paste_file(txt_name, "Backup 💾",None, display=display)


def snapshot(txt_name, unit, gap, trim = None, begin=0, display=True):
    """
    snapshot is a timed backup
    Takes a snapshot of the data file if certain time-based conditions are met.
    If `txt_name` is '*', the function backs up all files by calling 
    `core.select_star_copy_paste_folder()`. Otherwise, it backs up the specified 
    file using `core.cope_and_paste_file()` into the "Backup 💾" folder.

    Parameters:
    -----------
    txt_name : str
        The name of the text file (without extension) to snapshot.
        Must be a valid file name existing in the DB module.
    
    unit : str
        The unit of time to use when determining snapshot eligibility.
        Must be one of:
        ['s', 'second', 'm', 'min', 'minute', 'h', 'hour', 
         'd', 'day', 'mo', 'month', 'y', 'year']
    
    gap : int or float
        The time gap to wait before allowing the next snapshot.
        Must be a positive number.
    
    begin : int, optional (default=0)
        The starting hour of the day used for day-based snapshots.
        Must be between 0 and 23.
    
    display : bool, optional (default=True)
        Whether or not to display console output during execution.

    Returns:
    --------
    bool
        True if snapshot was taken successfully, False otherwise.

    Raises:
    -------
    ValueError
        If any of the parameters are invalid.
    """

    validations.snapshot_validate_parameters(txt_name, unit, gap, begin, display, trim)
    if txt_name == "*":
        core.select_star_copy_paste_folder(display,"Snapshots", trim)
    else:
        folder_path = core.resolve_txt_path_and_validation(txt_name)[0]
        date_change_path = os.path.join(folder_path, f'{txt_name}_snapshot.txt')

        if date_change.get(date_change_path, date_type=unit, time_gap=gap, day_start_hour=begin) == "A":
            core.cope_and_paste_file(txt_name, "Snapshot 📸", trim, display=display)


def debug(txt_name, is2d = None,clean = None, length = None, display = True):
    """
        Helps to scan through the selected file name to pin point where the validation
        issues are coming from

        if clean is set , it helps to automatically  updated the file after debug scan.
    """

    file_path = core.create_package_and_get_txt_folder_path(txt_name, position = "main")

    if display:
        print(f"\n🛡️ WithOpen | ⏳ Loading data ... [{datetime.now().strftime('%H:%M:%S')}]")
        time.sleep(3)
    
    if os.path.exists(file_path):

        others.debug_validation(txt_name, is2d , clean = clean, length = length, display = display)

        folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name)
        proposed_uncorrupted_data = wait_queue.wait_read(folder_path, txt_name, skip_memory_val = True)
        if proposed_uncorrupted_data:
            clean, unclean = others.get_debug_record(proposed_uncorrupted_data, is_2D = is2d, length =  length, display = display)
            if display:
                print("Done Debugging ✔️.")  
                
            return {"good": clean, "bad": unclean} # return debuged return 
    
        else:
            print("⚠️ You Can't Debug An Empty File.")
        
    else:
        print("The file path does not exist.")

    others.hide_hidden_files()

def remove(txt_name, display = True):
    # to delete a file from the DB
    
    if not isinstance(display, bool):
        raise TypeError("❌ The 'display' parameter must be a boolean value: either True or False.")
    list_dir = listdir(display = False)
    
    txt_name = core.clean_and_normalize_txt_name(txt_name)
    folder_path = core.create_package_and_get_txt_folder_path(txt_name)
    
    if txt_name not in list_dir:
        core.delete_empty_folder(folder_path) 
        raise FileNotFoundError(f"🛑 The file '{txt_name}' does not exist.")
        
    others.delete_path(folder_path, display = display)

def listdir(display = True):
    # To list all the files you have in your package dir
    
    if not isinstance(display, bool):
        raise TypeError("❌ The 'display' parameter must be a boolean value: either True or False.")

    return core.list_dir(display)

def hide(txt_name, display = True):

    if not isinstance(display, bool):
        raise TypeError("❌ The 'display' parameter must be a boolean value: either True or False.")

    list_dir = listdir(display = False)
    
    # to hide a file, if * add the full DB
    if txt_name.strip() == "*":
        folder_path =  core.get_main_package()
    else:
        folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name)
        if txt_name not in list_dir:
            core.delete_empty_folder(folder_path) 
            raise FileNotFoundError(f"The file '{txt_name}' does not exist in yet! .")
        a("__control_panel_987812919120", txt_name, is2d = False)
        
    action = control_file_visibility. hide_folder(folder_path)
    if display:
        print(action)

def unhide(txt_name, display = True):

    if not isinstance(display, bool):
        raise TypeError("❌ The 'display' parameter must be a boolean value: either True or False.")


    list_dir = listdir(display = False)
    
    # to unhide a file, if * add the full DB
    if txt_name.strip() == "*":
        folder_path =  core.get_main_package()
    else:
        folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name)
        if txt_name not in list_dir:
            core.delete_empty_folder(folder_path) 
            raise FileNotFoundError(f"The file '{txt_name}' does not exist in yet! .")
        try:
            d("__control_panel_987812919120", txt_name)
        except FileNotFoundError:
            pass
        
    action = control_file_visibility. unhide_folder(folder_path)
    if display:
        print(action)

def info(txt_name: str, display: bool = True) -> dict:
    #to get the info/describe a list

    if not isinstance(display, bool):
        raise TypeError("❌ The 'display' parameter must be a boolean value: either True or False.")

    others.info(txt_name, display) 


def consoles(txt_name, multiple, alert):
    #turn off or on mutiple consoles ...
    try:
        if not isinstance(multiple, bool):
            raise ValueError("The 'multiple' argument must be either True or False.")
        if not isinstance(alert, bool):
            raise ValueError("The 'display' argument must be either True or False.")
            
        txt_name = core.clean_and_normalize_txt_name(txt_name)
        folder_path = core.create_package_and_get_txt_folder_path(txt_name)
        consoles_path  = f"{txt_name}_consoles"
        core.write_all_files([multiple, alert] , folder_path, consoles_path, hide = True, single_write = True) #peform write  
    except FileNotFoundError:
        raise FileNotFoundError(f"🛑 The file '{txt_name}' does not exist.")
        
def warning(alert):
    # to hide alerting new/ warning that read isnt in consoles mode.   
    if not isinstance(alert, bool):
        raise ValueError("The 'multiple' argument must be either True or False.")

    console_mode_file = "__hide_new_alert_987812919120.txt"
    control_file_visibility. unhide_folder(console_mode_file)
    with open(console_mode_file, "w") as file:
        file.write(str((alert)))  # Writes them as a tuple string, e.g., "(True, False)"
    control_file_visibility. hide_folder(console_mode_file)
               
def help():

    # helper function to read the documentation summary
    
    mini_guide.help()
