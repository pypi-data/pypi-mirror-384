import datetime
import shutil
from . import mdb_wait_queue as wait_queue
import time


def check_matching_length(items):
    """
    Validates that all sublists in a list of lists have the same length.

    This function checks whether the input `items` is a 2D list (i.e., a list of lists),
    and ensures that each sublist has the same number of elements. If the input is a 
    1D list (i.e., not a list of lists), the function considers all elements as valid.

    Parameters:
        items (list): A list containing either:
            - a 1D list (e.g., [1, 2, 3]), or
            - a 2D list (e.g., [[1, 2], [3, 4]]), where all sublists must be the same length.

    Raises:
        ValueError: If any sublist has a different length from the first sublist.

    Example:
        check_matching_length([[1, 2], [3, 4]])   # Passes
        check_matching_length([[1, 2], [3]])      # Raises ValueError
    """
    if items:
        if not isinstance(items[0], list):
            validation = '1D'
        else:
            validation = len(items[0])
    
        for i, row in enumerate(items):
            if not isinstance(row, list):
                row_len = '1D'
            else:
                row_len = len(row)
    
            if row_len != validation:
                raise IndexError(
                    "Inconsistent row lengths passed in the parameter list: "
                    "all rows must have the same number of elements/length."
                )
    
        return validation 



def validate_delete_parameters_and_return_index(
    del_list: str | int | list,
    cutoff: int | None,
    keep: int | None,
    auto_trim_len: int | None,
    index: int | None | list,
    reverse: bool
) -> None:
    """
    Validates parameters used for trimming or deleting from a list.
    Ensures values are within expected types and constraints.
    returns index in as a list if not None 

    Args:
        del_list ( str | int | list)  items can't be empty.
        cutoff (int | None): Maximum number of items to delete (must be >= 1).
        keep (int | None): Number of items to retain (must be >= 0).
        auto_trim_len (int | None): Final length of the list after auto-trim (must be >= 0).
        index (int | None | list): Validate that index is None, an int, '*', or a list of ints.
        reverse (bool): Whether to process the list in reverse order.

    Raises:
        TypeError: If any parameter is not of the expected type.
        ValueError: If values violate logical constraints (e.g., both cutoff and keep set).
    """

    if auto_trim_len is not None:
        if auto_trim_len < 1:
            raise ValueError("⚠️ 'size' parameter must be greater than or equal to 1.")

    if not del_list and auto_trim_len is None:
        raise ValueError("del_list Parameter items can't be empty.")
        
    # cutoff must be int ≥ 1 or None
    if cutoff is not None:
        if not isinstance(cutoff, int):
            raise TypeError(f"cutoff must be an int or None, not {type(cutoff)}")
        if cutoff < 1:
            raise ValueError("cutoff must be at least 1")

    # keep must be int ≥ 0 or None
    if keep is not None:
        if not isinstance(keep, int):
            raise TypeError(f"keep must be an int or None, not {type(keep)}")
        if keep < 0:
            raise ValueError("keep cannot be negative")

    # Only one of cutoff or keep should be provided
    if keep is not None and cutoff is not None:
        raise ValueError("Arguments 'cutoff' and 'keep' cannot be passed at the same time.")

    # auto_trim_len must be int ≥ 0 or None
    if auto_trim_len is not None:
        if not isinstance(auto_trim_len, int):
            raise TypeError(f"auto_trim_len must be an int or None, not {type(auto_trim_len)}")
        if auto_trim_len < 0:
            raise ValueError("auto_trim_len cannot be negative")

    # Validate that index is None, an int, '*', or a list of ints.
    # Normalize index to always be a list of ints (unless it's '*' or None)
    if index is None:
        pass
    elif isinstance(index, int):
        index = [index]
    elif isinstance(index, list):
        if not all(isinstance(i, int) for i in index):
            raise TypeError("All elements in the index list must be integers.")
    elif index == '*':
        # Always a list; could be flat or 2D
        first_item_index = len(del_list[0]) if isinstance(del_list[0], list) else len(del_list)
        index = list(range(first_item_index))
    else:
        raise IndexError(
            f"index must be an int, '*', a list of ints, or None, not {type(index)}"
        )
    # if  index is an list and more than one  and del_list is a 1d list . covert del_list  to a 2dlist [del_list]
    if (
        isinstance(index, list)
        and len(index) > 1
        and not (
            isinstance(del_list, list)
            and all(isinstance(i, list) for i in del_list)
        )
    ):
        del_list = [del_list]

    # reverse must be boolean
    if not isinstance(reverse, bool):
        raise TypeError(f"reverse must be a bool, not {type(reverse)}")

    #---------------------------------------------------------------------------------------------

    row_len_check = check_matching_length(del_list)
    if del_list:
        if row_len_check != '1D' and index is None:
            raise IndexError(f"Index Requried..")

        """
        if row_len_check != '1D':
            if len(index) < len(del_list[0]):
                raise IndexError(f"confirm index paramter !! | Index Requried Not Complete.")
    
        # DB.d('jerry', [[10,'active'],['9', 'pending' ]] , index = [1,2,4] )
        if row_len_check != '1D':
            if len(index) != len(del_list[0]):
                raise IndexError("Inappropraite Indexing | Numbers of Indexes and Len of List Passed Must be equal.") 
        """
                    
    #---------------------------------------------------------------------------------------------

    # Normalize index to always be a list (unless it's '*')
    if index is None:
        return index, del_list
    else:
        return sorted(index) , del_list


def normalize_to_list(item):
    """
    Normalizes input to a list:
    - str, int, float, bool, None → [item]
    - tuple, set, frozenset, range → list(item)
    - dict → list of values
    - list → unchanged
    - other types raise TypeError
    - str is only allowed as a 1D or 2D list element, not directly
    """
    if isinstance(item, list):
        return item
    elif isinstance(item, (tuple, set, frozenset, range)):
        return list(item)
    elif isinstance(item, dict):
        return list(item.values())
    elif isinstance(item, (str, int, float)):
        return [item]
       #raise TypeError("A standalone string is not allowed. Expected a 1D or 2D list, not a plain string.")
    else:
        raise TypeError(f"Unsupported type: {type(item).__name__}. Expected a list-like structure.")

def normailize_to_2d (item, list2d):
    # if it detect it is a list and 2d was passed as the parmeter, it corrects it.
    if list2d is True:
        if isinstance(item, list) and all(not isinstance(i, list) for i in item):
            item = [item]
    return item


def corruption_tag(text: str, date: str = None, width: int = None) -> str:
    """
    Returns a centered string like ---[YYYY-MM-DD HH:MM:SS ©️ text]---,
    centered using explicit spaces (no str.center()).

    Parameters:
        text (str): The content to include.
        date (str, optional): Use a specific date (defaults to current datetime).
        width (int, optional): Total width of the final line (defaults to terminal width or 80).

    Returns:
        str: The centered line with spaces added manually.
    """
    if date is None:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        timestamp = date

    content = f"--- [ (c) {text} - Last Updated: {timestamp} | View Only - Editing Disabled ] ---"

    # Get terminal width
    if width is None:
        try:
            width = shutil.get_terminal_size().columns
        except:
            width = 80  # fallback default width

    padding_total = max(width - len(content), 0)
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left

    # Manually add spaces (empty " ") on left and right
    line = (" " * padding_left) + content + (" " * padding_right)

    return line


def snapshot_validate_parameters(txt_name: str, unit: str, gap: float, begin: int, display: bool, trim : bool) -> None:
    """
    Validates input parameters for a snapshot configuration.

    Parameters:
    ----------
    txt_name : str
        Name of the text file. Must be a non-empty string.
    
    unit : str
        Time unit for the snapshot interval. Accepted values are:
        ['s', 'second', 'm', 'min', 'minute', 'h', 'hour',
         'd', 'day', 'mo', 'month', 'y', 'year'].
    
    gap : int or float
        Interval between snapshots. Must be a positive number.
    
    begin : int
        Starting hour for snapshot, must be an integer between 0 and 23 inclusive.
    
    display : bool
        Flag indicating whether to display output. Must be a boolean.

    trim - trim must be an int ≥ 1 or None."

    Raises:
    ------
    ValueError
        If any parameter does not meet the required criteria.
    """

    if trim is not None:
        if not (isinstance(trim, int) and not isinstance(trim, bool) and trim >= 1):
            raise ValueError("trim must be an int ≥ 1 or None.")

    # Validate txt_name
    if not isinstance(txt_name, str) or not txt_name.strip():
        raise ValueError("Parameter 'txt_name' must be a non-empty string.")

    try:
        unit = unit.lower()  # Try to lowercase it first
    except:
        raise AttributeError(
            "Parameter 'unit' must be one of: "
            "['s', 'second', 'm', 'min', 'minute', 'h', 'hour', "
            "'d', 'day', 'mo', 'month', 'y', 'year']"
        )

    # Validate unit
    valid_units = [
        's', 'second', 'm', 'min', 'minute',
        'h', 'hour', 'd', 'day', 'mo', 'month', 'y', 'year'
    ]
    if unit not in valid_units:
        raise ValueError(
            "Parameter 'unit' must be one of: "
            "['s', 'second', 'm', 'min', 'minute', 'h', 'hour', "
            "'d', 'day', 'mo', 'month', 'y', 'year']"
        )

    # Validate gap
    if not isinstance(gap, (int, float)) or gap <= 0:
        raise ValueError("Parameter 'gap' must be numerical and greater than zero (0).")

    # Validate begin
    if not isinstance(begin, int) or not (0 <= begin <= 23):
        raise ValueError("Parameter 'begin' must be an integer between 0 and 23.")

    # Validate display
    if not isinstance(display, bool):
        raise ValueError("Parameter 'display' must be a boolean value.")

