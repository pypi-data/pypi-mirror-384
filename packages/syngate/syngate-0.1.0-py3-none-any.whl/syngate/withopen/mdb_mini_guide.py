def help():
    """
    🧾 WithOpen Quick Reference Guide
    ==================================

    ✅ STRUCTURE LOCKING
    ---------------------
    - On first `w()` or `a()`, structure is locked (1D or 2D + row length if 2D).
    - Future writes/appends must match saved structure.
    - To reset structure: use `w("file", [])`.

    📦 DATA STRUCTURE
    ---------------------
    - 1D: A simple list like `["apple", "banana"]`.
    - 2D: A list of lists like `[["apple", 1], ["banana", 2]]`.
    - Use `is2d=True/False` ONLY when writing/appending a new or resestted file.

    🧰 CORE FUNCTIONS (Usage & Parameters)
    =======================================

    ▶ w(txt_name, write_list, is2d=None)
       - Overwrites file with new data.
       - Args:
         • txt_name (str): Name of file.
         • write_list (list): New 1D/2D list to write.
         • is2d (bool | None): Required only if file is new or resetting.

    ▶ r(txt_name, index=None, set_new=[], notify_new=True) → list | None
       - Reads file content.
       - Args:
         • index (int | list | tuple): Return specific items/rows.
         • set_new ([] | None): Value to return if file doesn’t exist.
         • notify_new (bool): Notify if file is auto-created.

    ▶ a(txt_name, append_list, is2d=None) → list
       - Appends data to existing file.
       - Args:
         • append_list (list): Data to append (must match existing structure).
         • is2d (bool | None): Required only if file is new or resetting.

    ▶ d(txt_name, del_list=[], index=None, cutoff=None, keep=None, reverse=False, size=None) → (int, list)
       - Deletes matching entries or trims file.
       - Args:
         • del_list (list): Items to delete (["*"] deletes all).
         • index (int): Target column for deletion in 2D data.
         • cutoff (int): Max deletions per value.
         • keep (int): Keep this many rows per value.
         • reverse (bool): Process list in reverse.
         • size (int): Trim file to N most recent rows.
         
    ▶ backup(txt_name, display=True)
       - Creates a backup copy.
       - Use "*" to backup all files.

    ▶ snapshot(txt_name, unit, gap, trim=None, begin=0, display=True)
       - Takes time-based automatic backups.
       - Args:
         • unit (str): 's', 'm', 'h', 'd', 'mo', 'y'
         • gap (int/float): Min time between snapshots.
         • trim (int): Limit rows in snapshot.
         • begin (int): Start of day for daily snapshots (0-23).

    ▶ debug(txt_name, is2d=None, clean=None, length=None, display=True)
       - Scans file for validation issues and offers fixes.
       - Args:
         • clean (bool): Auto-fix file if errors are found.
         • length (int): Expected length of rows for 2D.

    ▶ info(txt_name, display=True)
       - Shows metadata: type, structure, shape, size, etc.

    ▶ consoles(txt_name, multiple: bool, alert: bool)
       - Enables or disables safe mode for multi-console interactions.
       - Args:
         • multiple (bool): True to allow multiple consoles/scripts.
         • alert (bool): Whether to show warnings during unsafe reads.

    ▶ warning(alert: bool)
       - Controls whether warnings should be shown when not in console-safe mode.

    ▶ remove(txt_name, display=True)
       - Permanently deletes a file and all backups.

    ▶ hide(txt_name, display=True) / unhide(txt_name, display=True)
       - Hides/unhides a file. Use "*" for all files.

    ▶ listdir(display=True) → list
       - Lists all current files.

    ▶ help(display=True)
       - Prints this guide.

    🔐 SYSTEM SAFETY
    -------------------------
    - Automatic file validation & hidden backups.
    - Warning issued for slow operations or unsafe access.
    - 3-level backup system for corruption recovery.
    - Hidden control files reduce manual tampering.

    🧠 TIPS
    -------------------------
    - Always use lists (1D or 2D).
    - Use `is2d=True` only when starting/resetting files.
    - Run `debug()` if structure errors or crashes occur.
    - `snapshot()` is ideal for long-running data logs.
    - Use `consoles()` to prevent race conditions when multiple scripts/tabs interact.

    📂 STORAGE FORMAT
    -------------------------
    - Data is stored in plain `.txt` files.
    - Folder structure automatically managed.
    - Compatible across platforms.
    - Backup and snapshot folders are neatly organized per file.

    🔚 End of Guide
    """
    print(help.__doc__)
