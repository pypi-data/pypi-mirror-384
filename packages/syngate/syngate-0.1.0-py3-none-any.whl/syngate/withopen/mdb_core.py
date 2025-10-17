import os
import ast
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import mdb_validations as validations
from . import mdb_control_file_visibility as control_file_visibility
import shutil
from datetime import datetime
import re
from . import mdb_others as others 
from . import mdb_wait_queue as wait_queue

parent_dir = current_dir = os.getcwd() 
backups = 3
package_name = "syngate_f"  # fixed folder name
CORRUPT_TAG = ['!!<<CORRUPT_DATA_BLOCK::UNRECOVERABLE::ID#e3f7!!>>']

# Prints a centered welcome message if 'MaxCleanerDB' is newly created.
# previously done by create_package_and_get_txt_folder_path def
main_package_path = os.path.join(current_dir, package_name)

if not os.path.exists(main_package_path):
    os.makedirs(main_package_path)

def get_main_package():
    # get the app/module main path
    return main_package_path 
  
def create_package_and_get_txt_folder_path(txt_name: str, position: str = "main") -> str:
    """
    Creates one of the folders 'MaxCleanerDB', 'MaxCleanerDB Snapshots', or 'MaxCleanerDB Backups'
    in the current working directory (where the function is called) if it doesn't exist.
    Returns the full absolute path to txt_name inside that folder.
    """
    current_dir = os.getcwd()      # Use the directory where the function is called

    folder_map = {
        "main": package_name,
        "snapshot": f"{package_name} Snapshots",
        "backup": f"{package_name} Backups"
    }

    if position not in folder_map:
        raise ValueError(f"Invalid position '{position}'. Must be one of: {list(folder_map.keys())}")

    folder_name = folder_map[position]
    package_path = os.path.join(current_dir, folder_name)

    full_txt_path = os.path.join(package_path, txt_name)
    return full_txt_path



def delete_empty_folder(path):
    """
    Deletes a folder and all its contents.

    Args:
        path (str): Path to the folder to delete.

    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    if os.path.isdir(path):
        try:
            # Remove folder and all its contents
            shutil.rmtree(path)
            return True
        except Exception as e:
            #print(f"Error deleting folder: {e}")
            return False
    return False

def clean_and_normalize_txt_name(txt_name: str) -> str:
    """
    Validates and normalizes a file name.

    - Removes trailing '.txt' if present.
    - Strips leading/trailing whitespace.
    - Rejects names containing '/', '\\', or '.' (after removing '.txt').

    Args:
        txt_name (str): The file name to clean and validate.

    Returns:
        str: A validated and cleaned file name.

    Raises:
        ValueError: If the file name contains invalid characters.
    """
    txt_name = txt_name.strip()

    # Remove .txt extension if present
    if txt_name.endswith('.txt'):
        txt_name = txt_name[:-4]

    # Blacklist characters that are not allowed (after removing '.txt')
    blacklist = ['\\', '/', '.']
    if any(char in txt_name for char in blacklist):
        raise ValueError("Invalid Txt_Naming Format: txt_name must not contain /, \\, or . (dot) | to hide use the update def.")

    return txt_name


def read_txt(file_path: str) -> list:
    """
    Reads a .txt file and parses its contents into a list.

    For each non-empty line in the file:
        - Attempts to evaluate the line as a Python literal (e.g., list, int, dict).
        - If parsing fails, keeps the line as a raw string.

    This approach allows mixed content in the file, such as both structured data
    and plain text, to be safely processed.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        list | None: A list of parsed lines, or None if the file doesn't exist 
        or contains no non-empty lines.
    """
            
    if not os.path.exists(file_path):
        return None
    
    results = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                parsed_line = ast.literal_eval(line)
            except (SyntaxError, ValueError):
                parsed_line = line  # Keep original line if it can't be evaluated
            results.append(parsed_line)

    # corruption test.
    if results:
        if isinstance(results[0], str) and results[0].startswith('--- [ (c)'):
            return results[1:]
            
        else:
            return CORRUPT_TAG
    else:
        return None

'''

def normal_write_file(file_path, content , skip_hide = True):
    """
    Writes a string to a file.

    direct except was intentional this file read validataion.
    any form of error go as None and it will be solve during resolve_txt_path_and_validation.
    
    Parameters:
    - file_path (str): Full path to the file.
    - content (str): The string content to write.
    """
    
    content = str(content)
    
    if not content:
        conetnt = 'n'+'n'+ validations.corruption_tag(package_name)
    else:
        content += '\n'+'\n'+validations.corruption_tag(package_name)

    
    control_file_visibility.unhide_folder(file_path)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(content))
    except:
        control_file_visibility.hide_folder(file_path)
        return None
    control_file_visibility.hide_folder(file_path)

'''

def resolve_txt_path_and_validation(txt_name, skip_validation_error = False):
    """
    Prepares and returns the working environment for a given text file name.

    This function is used across read, write, append, and delete operations. It:
        - Validates and normalizes the provided text file name.
        - Ensures the target folder exists (creating it if necessary).
        - Constructs the path to the validation file.
        - Loads the validation data (if it exists).

    Args:
        txt_name (str): The base name of the text file (without invalid characters or '.txt').

    Returns:
        tuple:
            - folder_path (str): Full path to the folder where the text files are stored.
            - read_validation (list | None): Parsed content of the validation file, 
              or None if the file doesn't exist.
            - validation_path (str): Full path to the validation file.

    Raises:
        ValueError: If the text name contains disallowed characters such as '/', '\\', or '.'.
    """

    txt_name = clean_and_normalize_txt_name(txt_name)
    folder_path = create_package_and_get_txt_folder_path(txt_name)
    control_file_visibility.unhide_folder(folder_path) # make sure the file is open
    os.makedirs(folder_path, exist_ok=True)

    validation_path = validation_name = f'{txt_name}_validation'

    #--------- from pressure test validation seems to output none if ourload while on wait queue
 
    MAX_RETRIES = 3
    read_validation = None
    for _ in range(MAX_RETRIES):

        try:
            read_validation = majority_vote_file_reader(validation_name, folder_path)
        except ValueError:
            read_validation = None
        if read_validation:
            break
        time.sleep(0.003)
    #----------------------------------------------------------------------------------------------
    
    validation = read_validation[0]if read_validation else None
    
    if validation != '1D' and not isinstance(validation, int):
        if skip_validation_error:
            validation = None
        else:
            if os.path.isdir(validation_path):
                raise ValueError(f"🛑 Validation Error: Corrupted Validation Tag | ")

    return folder_path, validation_path, validation

def validate_and_register_row_shape(folder_path, items: list, validation: int | str | None, validation_path: str , list2d = None) -> None:
    """
    Validates that all rows in a list have consistent lengths.

    - If validation is not provided, infers it from the first item.
    - Handles both 1D and 2D data.
    - Writes the inferred length to a validation file if it's the first write.

    Args:
        items (list): A list of elements or sublists to validate.
        validation: Expected length of each row, or None to infer it.
        validation_path (str): Path to write validation data if it's a new file.

    Raises:
        ValueError: If any row length differs from the first row's length.
    """

    
    def is_2d_list(lst):
        # Check first first items
        for item in lst[:1]:
            if not isinstance(item, list):
                return False
        return True

    first_write = False
    if validation is None:
        if items:
            if not isinstance(items[0], list):
                validation = '1D'
            else:
                validation = len(items[0])
        first_write = True

    validated = True
    main_items =items
    for error_counter in range(3):

        try:
            for i, row in enumerate(items):
                if not isinstance(row, list):
                    row_len = '1D'
                else:
                    row_len = len(row)
        
                if row_len != validation:
                    if error_counter == 0:
                        items = [items]
                        validated = False
                        break
                    elif error_counter == 1:
                        if len(main_items) == 1:
                            items = main_items[0]
                            validated = False
                            break
                    else:
                        raise ValueError(
                            f"Inconsistent row lengths Passed in the Parameter list at row {i}:\n"
                            f"            Expected {validation} Length but got {row_len} => {row}.\n"
                        )
        except TypeError:
            raise ValueError(
                f"Inconsistent row lengths Passed in the Parameter list at row {i}:\n"
                f"            Expected {validation} Length but got {row_len} => {row}.\n"
            )
            
    
        if validated == True:
            break

    if first_write is True:
        # print("⚠️ New File | If this is not a New file, kindly confirm the validation manually.")
        is_2d = is_2d_list(items)
        
        if is_2d is False and list2d is None: 
            delete_empty_folder(folder_path) # folder was already created , so delete.
            raise ValueError(
                "🟡 1D data detected. On first write or after a reset, setting parameter [ is2d=False ].\n"
                "               This prevents incorrect structure locking for a 2D file created inside a loop.\n"
                "               This action/parameter is only needed when a 1D list is passed at creation or reset.\n"
                "               Auto-correct only works after you've initialized the file (That is after proper first a write or append.)"
            )
        elif is_2d is False and  list2d is True: 
            delete_empty_folder(folder_path) # folder was already created , so delete.
            raise ValueError("⚠️ 'is2d=True' was set, but the data appears 1D. \n"
                             "                If you're trying to create a 2D structure, wrap your list in an extra bracket like [[...]].\n"
                             "                This action/parameter is only needed when a 1D list is passed at creation or reset.\n"
                             "                Auto-correct only works after you've initialized the file (That is after proper first a write or append.)"
                            )
    
        write_all_files([validation], folder_path, validation_path, hide=True)

    return items



def write_all_files(write_list, folder_path, txt_name, single_write=False, hide=False):
    """
    Creates one or more backup files by writing the same content to each.

    Parameters:
        write_list (list or None): Items to write. Each item is converted to a string (including None as 'None').
        folder_path (str): Directory where files will be saved.
        txt_name (str): Base name of the text file.
        single_write (bool): If True, write only one file (no backups).
        hide (bool): If True, hide the file(s) after writing.

    Notes:
        - 'backups' must be defined globally.
        - 'get_final_txt_path_dest' is used to generate file paths.
        - 'validations.corruption_tag' is appended to file content.
        - 'control_file_visibility' is used to hide/unhide files.
    """

    # Normalize input
    if write_list is None:
        lines = ['None']
    else:
        lines = [str(x) for x in write_list]

    # Join and add corruption tag
    write_str = validations.corruption_tag(package_name) + '\n\n' + '\n'.join(lines)
    # Write files
    if single_write:
        backups = 1
    else:
        backups = 3

    for i in range(backups):
        final_dest_path = get_final_txt_path_dest(i, folder_path, txt_name)

        if i > 0 or hide:
            control_file_visibility.unhide_folder(final_dest_path)

        with open(final_dest_path, 'w', encoding='utf-8') as f:
            f.write(write_str)

        if i > 0 or hide:
            control_file_visibility.hide_folder(final_dest_path)


def read_files_concurrently(file_paths: list[str], max_workers: int = 5) -> list:
    """
    Reads multiple files concurrently using ThreadPoolExecutor.

    Args:
        file_paths (list): List of file paths to read.
        max_workers (int): Maximum number of threads to use.

    Returns:
        list: Contents of the files in the same order as `file_paths`.
    """
    results = [None] * len(file_paths)

    def read_task(index, path):
        return index, read_txt(path)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(read_task, i, path) for i, path in enumerate(file_paths)]

        for future in as_completed(futures):
            index, content = future.result()
            results[index] = content

    return results

def most_common_row(list_of_lists):
    """
    Finds the most frequent row based on stringified values.
    Converts each element to string for comparison,
    then evals the most common row twice to restore data types.
    """

    def safe_literal_eval(value):
        """
        Tries to ast.literal_eval a string value.
        Falls back to original if it fails (e.g. 'jef' is not quoted).
        """
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value
    #Start✅
    if not list_of_lists:
        return []

    # Step 1: Normalize all rows by converting each element to str
    str_rows = [str([str(item) for item in row]) for row in list_of_lists]

    # Step 2: Count frequency
    count = Counter(str_rows)
    max_freq = max(count.values())
    most_common = [row for row, freq in count.items() if freq == max_freq]

    # Step 3: Raise error if tie
    if len(most_common) > 1:
        parsed_rows = [ast.literal_eval(row) for row in most_common]
        raise ValueError(
            f"Corrupted data: tie in most common rows with frequency {max_freq}: {parsed_rows}"
        )

    # Step 4: Eval once to get list of strings
    first_eval = ast.literal_eval(most_common[0])

    # Step 5: Safely eval each item to restore its type (int, float, etc.)
    second_eval = [safe_literal_eval(item) for item in first_eval]

    return second_eval
    

def get_final_txt_path_dest(i, folder_path, txt_name):
    """
    Generates file path for primary and backup files.

    Args:
        i (int): Backup index (0 = main file, 1 = first backup, etc.).
        folder_path (str): The directory where the file should be saved.
        txt_name (str): Base name of the file (without extension).

    Returns:
        str: The full file path with appropriate suffix.
    """

    # Main file has no suffix; backups are numbered
    file_name = f"{txt_name}.txt" if i == 0 else f"{txt_name}_{i}.txt"
    
    return os.path.join(folder_path, file_name)



def majority_vote_file_reader(txt_name: str, folder_path: str, retries: int = 2, delay: float = 0.01, single_read = False) -> list | None:
    """
    Reads multiple backup files concurrently and returns the most commonly occurring file content.
    Retries up to `retries` times if the result is empty or None.

    newlday added pause enable to mark wait queue heartbeat

    Parameters:
        txt_name (str): The name of the file to read.
        folder_path (str): The path to the folder containing the backup files.
        retries (int): Number of retries if the result is empty or None.
        delay (float): Delay (in seconds) between retries.

    Returns:
        list | None:
            - A list representing the most common file content if found.
            - `None` if all backups are missing after retries.
            - An empty list if no consensus is reached.
    """
    for attempt in range(retries):
        all_file_records = []

        if single_read:
            backups = 1
        else:
            backups = 3
            
    
        files_to_thread = [get_final_txt_path_dest(i, folder_path, txt_name) for i in range(backups)]
   
        queue_id = f"{txt_name}_queue"
        all_file_records = read_files_concurrently(files_to_thread)

        # Check 1: All files missing
        if all(item is None for item in all_file_records):
            result = None
        else:
            filtered_all_file_records = [row for row in all_file_records if row is not None]
            txt_read = most_common_row(filtered_all_file_records)

            # Check 2: Most common row not found
            if not txt_read:
                result = []
            elif txt_read == CORRUPT_TAG:
                full_path = os.path.join(folder_path, txt_name) 
                raise ValueError(
                    f"🛑 File corruption or tampering detected.\n\n"
                    f"Please follow these steps to inspect and fix the issue:\n\n"
                    f"1. 📂 Confirm the file path:\n"
                    f"   {full_path}\n\n"
                    f"2. 🧾 Manually read the file content:\n"
                    f"   Example in Python:\n"
                    f"       with open(r'{full_path}', 'r', encoding='utf-8') as f:\n"
                    f"           print(f.read())\n\n"
                    f"3. 🛠️ Fix any content issues you find.\n"
                    f"   You can use a text editor or overwrite the file programmatically.\n\n"
                    f"4. ⚠️ for safety Backup the file elsewhere before deleting.\n\n"
                    f"5. 🗑️ Delete the corrupted file:\n"
                    f"       f.remove(\"{txt_name}\")\n\n"
                    f"6. ✅ Save your corrected version with the same filename.\n"
                    f"   Make sure the structure and content are valid before reuse."
                )

            else:
                return txt_read  # ✅ Valid result

        # Retry condition: if result is falsy
        if result:
            return result

        time.sleep(delay)  # wait before retry

    return result  # After retries, return whatever final result we have (None or [])

def get_keep_deletion_rules_filter(file, index, cleaned_list, keep):
    """
    cleaned_list or str_del_list
    
    Determines which items to retain or delete based on frequency and 'keep' value.

    Args:
        file (list): The list of records (can be 1D or 2D).
        index (int | None): Index used to extract values for comparison.
        cleaned_list (list): Items being considered for deletion.
        keep (int): Number of allowed duplicates to retain.

    Returns:
        list: List of items that exceed the 'keep' threshold and should be deleted.
    """
    # Get the specific column/index for comparison if index is provided
    if index: # is not None and index >= 0:
        index_only = []
        for x in file:
            #select here mimic sql select
            for i,select_index in enumerate(index):
                if i == 0:
                    select = str(x[select_index])
                else:
                    select += str(x[select_index])
                index_only.append(select)
    else:
        index_only = [ str(x) for x in file ]

    # Count frequency of each value
    index_count = []
    for x in index_only:
        if x not in [ x[0] for x in index_count ]:
            if x in cleaned_list:
                index_count.append( [ x , index_only.count(x) ] )

    # Determine how many occurrences to remove
    cleaned_list = []   
    for x in index_count:
        keep_calculator_with_negative = x[1] - keep
        keep_calculator = (
            0 if keep_calculator_with_negative <= 0
            else keep_calculator_with_negative
        )
        cleaned_list  += ([x[0]] * keep_calculator)
    return cleaned_list

def delete_heart(file, cleaned_list, index, adjusted_index, cutoff, keep):
    """
    adjusted_index or is_2D
    cleaned_list or str_del_list
    
    Core delete logic that removes items based on cleaned_list, index, and limits.

    Args:
        file (list): The original list to process.
        cleaned_list (list): The items to delete.
        index (int): Index to use if working with 2D lists.
        adjusted_index (bool): Whether to treat elements as 1D items wrapped in a list.
        cutoff (int | None): Max number of deletions per value.
        keep (int | None): Number of items to retain.

    Returns:
        tuple: A tuple containing:
            - list: Items that remain after deletion.
            - int: Number of deletions performed.
    """

    def del_limit_reset(del_list: list[str], remove_from_del_list: str) -> list[str]:
        """
        Removes one occurrence of a value from a deletion list.
    
        Args:
            del_list (list[str]): List of values marked for deletion.
            remove_from_del_list (str): Value to remove from the list.
    
        Returns:
            list[str]: Updated deletion list.
        """
        del_index = None
        for i, x in enumerate(del_list):
            if remove_from_del_list == x:
                del_index = i
                break   
        del_list.pop(del_index)
        
        return del_list

    delete_counter = 0
    non_del_list = []
    if not cleaned_list :
        non_del_list = file
    else:
        for x in file:
            if adjusted_index == True:
                select = str(x)
            else:
                #the concantuate is like an and function when deleting.
                for i,select_where in enumerate(index):
                    try:
                        if i == 0:
                            select = str(x[select_where])
                        else:
                            select += str(x[select_where])
                    except IndexError:
                        raise IndexError("🚫 Your File List not up to this index/row_length")
            if select in cleaned_list:
                delete_counter += 1
                if cutoff or keep:
                    del_list = del_limit_reset ( cleaned_list , select) # this is for limit when and item is delete it removes from it limit
            else:
                if adjusted_index == True:
                    non_del_list.append(x)
                else:   
                    non_del_list.append(x)
                    
    return non_del_list, delete_counter


def copy_folder(old_path, new_path, display, action_type):
    """
    Copies a folder from old_path to new_path.

    Parameters:
    - old_path (str): The path to the existing folder.
    - new_path (str): The path where the new folder should be created.

    Raises:
    - FileNotFoundError: If the old_path does not exist.
    - FileExistsError: If the new_path already exists.
    """
    if not os.path.exists(old_path):
        raise FileNotFoundError(f"Source folder does not exist: {old_path}.")
    
    if os.path.exists(new_path):
        raise FileExistsError(f"Destination folder already exists: {new_path}.")

    shutil.copytree(old_path, new_path)
    if display:
        print(f"General (*) {action_type} Successfully Done ✅.")

def create_named_path(name: str) -> str:
    """
    Generate a unique timestamped filename based on current datetime and given name.

    Parameters:
    -----------
    name : str
        Base name of the file.

    Returns:
    --------
    str
        Timestamped filename ending in `.txt`.
    """
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    name_with_timestamp = f"{timestamp}_{name}"
    return name_with_timestamp

def select_star_copy_paste_folder(display, action_type, trim):

    #Use it to for backup and snaps to get the full app.
    
    copy_path = package_path = os.path.join(parent_dir, package_name)
    paste_folder = package_path = os.path.join(parent_dir, f"{package_name} All {action_type}")

    others.trim_subfolders(paste_folder, trim) #trim snaps folder
    
    if not os.path.exists(paste_folder):
        os.makedirs(paste_folder)

    paste_path = os.path.join(paste_folder, create_named_path(package_name))

    copy_folder(copy_path, paste_path, display, action_type[:-1])


def cope_and_paste_file(txt_name: str, action_type: str, max_files: int, display: bool = True) -> bool:
    """
    Create a backup or snapshot of a text-based file.

    This function retrieves the data associated with a given file name (`txt_name`) 
    and writes it to a new file inside a designated backup or snapshot folder. 
    The file is timestamped to ensure versioning.

    Parameters:
    -----------
    txt_name : str
        The name of the text file to back up or snapshot.
        
    type : str
        The type of operation to perform. Accepts:
            - "Backup 💾"
            - "Snapshot 📸"
            
    display : bool, optional (default=True)
        If True, display messages indicating success or failure.

    Returns:
    --------
    bool
        True if the operation completes successfully or file is empty,
        False if the named file does not exist in the database.
    """
    try:
        # varibale name update fix
        type = action_type
    except:
        pass
        
    folder_path, validation_path, validation = resolve_txt_path_and_validation(txt_name)
    data = majority_vote_file_reader(txt_name, folder_path)

    if data:
        if action_type == "Backup 💾":
            get_backup_path = create_package_and_get_txt_folder_path(txt_name, position = "backup")
        elif action_type == "Snapshot 📸":
            get_backup_path = create_package_and_get_txt_folder_path(txt_name, position = "snapshot")

        others.trim_folder_files(get_backup_path, max_files) #trim snaps folder
            
        if not os.path.exists(get_backup_path):
            os.makedirs(get_backup_path)

        backup_name = create_named_path(txt_name)
        if not os.path.exists(get_backup_path):
            os.makedirs(get_backup_path)

        write_all_files(data, get_backup_path, backup_name, single_write=True)
        if display:
            print(f"{action_type} Successfully Done ✅.")
        return True
        
    elif data is None:
        delete_empty_folder(folder_path)
        raise FileNotFoundError(f"The file '{txt_name}' does not exist in yet! .")
        if display:
            pass
            #print("❌ Invalid Name as File Doesn't Exist Yet.")
            
        return False

    elif data == []:
        print(f"🚫 Can't {action_type} An Empty File.")
        return True


def list_dir(display=True):
    try:
        all_items = os.listdir(package_name)
        # Only include folders, exclude hidden or special folders
        folders = [
            item for item in all_items
            if os.path.isdir(os.path.join(package_name, item)) and
               not item.startswith('.') and
               not item.startswith('__') and
               not item.endswith('__')
        ]

        if display:
            print(f"Visible folders in directory '{package_name}':")
            print(f"Total files: {len(folders)}")
            for folder in folders:
                print(f" - {folder}")
            
        return folders

    except FileNotFoundError:
        if display:
            print(f"Directory not found: {package_name}")
        return []
    except NotADirectoryError:
        if display:
            print(f"Not a directory: {package_name}")
        return []
    except PermissionError:
        if display:
            print(f"Permission denied: {package_name}")
        return []

