from .mdb_ScreenBuffer import ScreenBuffer
from . import mdb_pretty_print as pretty_print 
import time
from . import mdb_loop_progress as loop_progress 
import os
import shutil
from . import mdb_core as core
from . import mdb_control_file_visibility as control_file_visibility
from datetime import datetime
from . import main as main
import glob


def get_debug_record(lst, is_2D, display, length):

    """
    Validates and filters a list (1D or 2D) while providing a dynamic debug display
    using ScreenBuffer. Primarily used in MaxCleanerDB to visualize and debug
    data structure inconsistencies.

    Parameters:
    ----------
    lst : list
        The list to validate. Can be a 1D list or a 2D list (list of lists).
    
    is_2D : bool
        Indicates whether the expected structure of `lst` is 2D (True) or 1D (False).
        - If True: validates that each element is a list of a specific `length`.
        - If False: validates that each element is **not** a list.
    
    show : bool
        If True, displays messages for invalid records as they are processed.
        These messages are shown in the ScreenBuffer output area.
    
    length : int
        Applicable only when `is_2D` is True.
        Used to validate that each inner list in the 2D structure matches this length.
    
    Returns:
    -------
        list
                A new list (`cleaned`) containing only the valid records that passed structural validation.
    """

    def get_screen (wait, start = True):
        message = '\n   🛡️ WithOpen Debug Mode.'
        message = pretty_print.stylize (message, bold=True )
        return ScreenBuffer(
            wait = wait,
            max_wait = 9,
            max_display = 8,
            start = start,
            header = message,
            header_alignment = 2,
            show_header = True,
            silent_display = None,
            only_display = None,
            auto_clean_edges = True,
            auto_clean_silent_only_display = False,
            shift_max_display = True  
        )

    screen = get_screen(True) #get your screenbuffered screen
    
    if not isinstance(lst, list):
        screen.put("❌ Major Issue | This file is not a list.")
        screen.put("🛠️ Manual Inspection Required.")
        screen.put("To Solve This")
        screen.put("Step 1 - Move file to MaxCleanerDB backup location using the backup def/function [ MaxDBcleaner.backup(filename) ].")
        screen.put("Step 2 - Get the content manually using [ with open( filepath, "r") as f ] to clean/debug it.")
        screen.put("Step 3 - Reset the file validation using [ MaxCleanerDB.w(filename, []) ]")
        screen.put("Step 4 – Now move the manually cleaned file into the orignal file you just reset validation for.")
        return False
    
    def create_trimmable_list(trim_len):
        lst = []
    
        def add_or_get(item=None):
            nonlocal lst
            if item is not None:
                lst.append(str(item))
                if len(lst) > trim_len:
                    lst = lst[-trim_len:]
            return "\n".join(lst)
    
        return add_or_get
        
    add_to_list = create_trimmable_list(3)
    cleaned = []
    unclean = []
    total = len(lst)

    for i, item in enumerate(lst):
        long_pause = False
            
        if is_2D:
            if isinstance(item, list):
                if len(item) == length:
                    cleaned.append(item)
                else:
                    long_pause = True
                    add_to_list(f"Row {i} mismatch inner list/2D length: {str(item)}")
                    unclean.append(item)
            else:
                long_pause = True
                add_to_list(f"Row {i} mismatch (Not a 2D list): {str(item)}")
                unclean.append(item)
        else:
            if not isinstance(item, list):
                cleaned.append(item)
            else:
                long_pause = True
                add_to_list(f"Row {i} mismatch (Not a 1D List): {str(item)}")
                unclean.append(item)

        #------------------------------------------------------------------------------------------

        valid = len(cleaned)
        invalid = len(unclean)

        i += 1
        try:
            percent_valid = (valid / i * 100)
        except ZeroDivisionError:
             percent_valid = 0

        try:
            percent_invalid = (invalid / i * 100)
        except ZeroDivisionError:
            percent_invalid = 0

        #------------------------------------------------------------------------------------------

        screen.put(f"🧮  Total  : {total:,}", index = 0)
        screen.put(f"❌ Invalid : {invalid:,} ({round(percent_invalid)}%)", index = 1)

        screen.put(f"✅  Valid  : {valid:,} ({round(percent_valid)}%)", index = 2)
        screen.put ("", index = 3)

        screen.put(add_to_list(), index = 4 )
        screen.put("", index = 5)
        screen.put(loop_progress.get(i, total), index = 6)

        if display is True:
            screen.display()
            if long_pause:
                time.sleep(1)
            else:
                time.sleep(0.01)
            
    return cleaned, unclean


def debug_validation(txt_name, is_2D, clean=None, length=None, display=True):
    # Validate txt_name
    if not isinstance(txt_name, str):
        raise TypeError("txt_name must be a string.")

    # Validate is_2D
    if not isinstance(is_2D, bool):
        raise TypeError("is2d must be a boolean.")

    # Validate display
    if not isinstance(display, bool):
        raise TypeError("display must be a boolean.")

    # Validate clean (optional)
    if clean is not None and not isinstance(clean, bool):
        raise TypeError("clean must be a boolean if provided.")

    # Validate length based on is_2D
    if is_2D:
        if length is None:
            raise ValueError("length must be provided when is2d is True.")
        if not isinstance(length, int):
            raise TypeError("length must be an integer when is2d is True.")
        if length <= 0:
            raise ValueError("length must be greater than zero when is2d is True.")


def delete_path(path, display=True):
    
    # to delete a folder with it paths
    
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
        if display:
            print(f"File or symlink deleted: {path}")
    elif os.path.isdir(path):
        shutil.rmtree(path)
        if display:
            print(f"Directory deleted: {path}")
    else:
        if display:
            print(f"Path does not exist: {path}")



def hide_hidden_files():

    # To  Make sure  all hidden files set for hidden are hidden.
    # this is because if a program is interuppted before ending it exposes the txt.
    
    control_panel_name = "__control_panel_987812919120"
    control_panel_folder_path = core.resolve_txt_path_and_validation(control_panel_name, skip_validation_error = True)[0]
    control_file_visibility.unhide_folder(control_panel_folder_path)
    read_control_panel = core.majority_vote_file_reader(control_panel_name, control_panel_folder_path)
    control_file_visibility.hide_folder(control_panel_folder_path) # hide back immediately

    if read_control_panel:
        for hidden_txt in read_control_panel:
            hiiden_file_path = core.resolve_txt_path_and_validation(hidden_txt, skip_validation_error = True)[0]
            control_file_visibility.hide_folder(hiiden_file_path)



def smart_select(data, index):
    """
    Select elements from a 1D or 2D list based on the given index or indexes.

    Parameters:
    ----------
    data : list
        A list of values (1D) or a list of lists/tuples (2D).
    index : int, list, tuple
        - If data is 1D:
            - int: returns the element at that index.
            - list/tuple of ints: returns the elements at those indices.
        - If data is 2D:
            - int: selects that column index from each row.
            - list/tuple of ints: selects those column indices from each row.

    Returns:
    -------
    list or element
        - A single element if 1D with int index.
        - A list of selected elements otherwise.

    Raises:
    ------
    TypeError:
        If index is not an int, list, or tuple.
    IndexError:
        If any index is out of range for the given data structure.
    """

    # Validate index type
    if not isinstance(index, (int, list, tuple)):
        raise TypeError("Index must be an int, list, or tuple. Please confirm the index given.")

    is_2d = isinstance(data[0], (list, tuple))

    try:
        if is_2d:
            if isinstance(index, (list, tuple)):
                # Multiple elements from each row
                return [[row[i] for i in index] for row in data]
            else:
                # Single element from each row
                return [row[index] for row in data]
        else:
            if isinstance(index, (list, tuple)):
                return [data[i] for i in index]
            else:
                return data[index]
    except IndexError:
        raise IndexError("One or more indexes are out of range. Please confirm the index given in the parameter.")



def info(txt_name: str, display: bool = True) -> dict:
    """
    Displays or returns metadata about a file stored in MaxCleanerDB.

    Parameters:
        txt_name (str): Base name of the txt file (without .txt extension).
        display (bool): If True, prints the information. Otherwise, returns a dictionary.

    Returns:
        dict: Metadata about the file.
    """
    import glob

    package_name = core.get_main_package()
    list_dir = main.listdir(display = False)

    # Get validation and data
    folder_path, validation_path, validation = core.resolve_txt_path_and_validation(txt_name, skip_validation_error=True)

    if txt_name not in list_dir:
        core.delete_empty_folder(folder_path) 
        raise FileNotFoundError(f"The file '{txt_name}' does not exist in yet! .")
            
    data = core.majority_vote_file_reader(txt_name, folder_path)

    # --- Determine Structure ---
    if data is None:
        structure = "Not Found"
    elif data == []:
        structure = "Empty"
    elif isinstance(validation, int):
        structure = "2D"
    elif validation == "1D":
        structure = "1D"
    else:
        structure = "Unknown"

    entry_count = len(data) if isinstance(data, list) else 0
    row_validation = validation if validation else "-"

    # --- Paths ---
    current_dir = os.getcwd()
    main_path = os.path.join(current_dir, f"{package_name}\\{txt_name}")
    backup_path = os.path.join(current_dir, f"{package_name} Backups\\{txt_name}")
    snapshot_path = os.path.join(current_dir, f"{package_name} Snapshots\\{txt_name}")

    # --- Count Backups ---
    backup_files = glob.glob(os.path.join(backup_path, "*.txt")) if os.path.exists(backup_path) else []
    backup_count = len(backup_files)

    # --- Count Snapshots ---
    snapshot_files = glob.glob(os.path.join(snapshot_path, "*.txt")) if os.path.exists(snapshot_path) else []
    snapshot_count = len(snapshot_files)

    # --- Last snapshot timestamp ---
    if snapshot_files:
        latest_snapshot = max(snapshot_files, key=os.path.getmtime)
        snapshot_date = datetime.fromtimestamp(os.path.getmtime(latest_snapshot)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        snapshot_date = "—"

    # --- Result Dictionary ---
    result = {
        "Structure": structure,
        "Total Entries": entry_count,
        "Row Validation": row_validation,
        "Backups": backup_count,
        "Snapshots": snapshot_count,
        "Last Snapshot": snapshot_date,
        "Main Path": main_path,
        "Backup Path": backup_path,
        "Snapshot Path": snapshot_path,
    }

    if display:
        structure_display_map = {
            "1D": "📄 Structure: 1D list",
            "2D": "🧱 Structure: 2D list",
            "Empty": "🟤 Empty File",
            "Not Found": "🔴 File Not Found",
            "Unknown": "❓ Unknown Structure"
        }

        print(f"\n{structure_display_map.get(structure, '❓ Unknown Structure')}")
        print(f"🗃️ Total Entries: {entry_count}")
        print(f"🧠 Row Validation: {row_validation}")
        print()
        print("🛟 Backup/Snapshot Status:")
        print(f"  🔁 Backups:   {backup_count}")
        print(f"  📸 Snapshots: {snapshot_count}")
        print(f"  🕒 Last Snapshot: {snapshot_date}")
        print()
        print("📁 Folder Paths:")
        print(f"  📂 Main Path:     {main_path}")
        print(f"  💾 Backup Path:   {backup_path}")
        print(f"  📸 Snapshot Path: {snapshot_path}")
        print()

    return result


def trim_folder_files(path, max_files):
    """
    Ensures that the folder at 'path' contains at most 'max_files'.
    If there are more, it deletes the oldest files.
    
    Args:
        path (str): Path to the folder to check.
        max_files (int): Maximum number of files allowed in the folder.

    """
    if  max_files is not None:
    
        if os.path.isdir(path):
            
            # Get all files (ignore subfolders)
            files = [f for f in glob.glob(os.path.join(path, "*")) if os.path.isfile(f)]
        
            # If number of files is within limit, do nothing
            if len(files) <= max_files:
                # print(f"No action needed. {len(files)} file(s) found, limit is {max_files}.")
                return
        
            # Sort files by modification time (oldest first)
            files.sort(key=os.path.getmtime)
        
            # Delete the oldest files
            num_to_delete = len(files) - max_files
            for i in range(num_to_delete):
                try:
                    os.remove(files[i])
                    # print(f"Deleted: {files[i]}")
                except Exception as e:
                    print(f"Error deleting {files[i]}: {e}")


def trim_subfolders(path, max_folders):
    """
    Ensures that the folder at 'path' contains at most 'max_folders' subdirectories.
    If there are more, it deletes the oldest ones.

    Args:
        path (str): Path to the parent folder.
        max_folders (int): Maximum number of subfolders allowed in the parent folder.
    """
    if max_folders is not None:
        if os.path.isdir(path):
            # Get all immediate subdirectories (ignore files)
            folders = [f for f in glob.glob(os.path.join(path, "*")) if os.path.isdir(f)]

            # If number of folders is within limit, do nothing
            if len(folders) <= max_folders:
                #print(f"No action needed. {len(folders)} folder(s) found, limit is {max_folders}.")
                pass
                return

            # Sort folders by modification time (oldest first)
            folders.sort(key=os.path.getmtime)

            # Delete the oldest folders
            num_to_delete = len(folders) - max_folders
            for i in range(num_to_delete):
                try:
                    shutil.rmtree(folders[i])
                    # print(f"Deleted folder: {folders[i]}")
                except Exception as e:
                    print(f"Error deleting folder {folders[i]}: {e}")

