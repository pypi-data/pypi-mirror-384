import os
import time

def clear_output(wait=True, delay=0.1):
    """
    Clears the screen in a terminal or Jupyter Notebook.
    
    Parameters:
    - wait (bool): If True, wait before clearing (default True).
    - delay (float): Delay before clearing, in seconds.
    """
    try:
        if wait:
            time.sleep(delay)

        # Check if in Jupyter/IPython
        from IPython import get_ipython
        shell = get_ipython()
        if shell is not None and "IPKernelApp" in shell.config:
            from IPython.display import clear_output as ipy_clear
            ipy_clear(wait=wait)
        else:
            os.system('cls' if os.name == 'nt' else 'clear')

    except Exception as e:
        print(f"Clear output failed: {e}")


def wipe_screen (wait=True , delay = 0.1) :
    """
    Clear output in Jupyter or terminal.

    Parameters:
    - wait (bool): if True, wait before clearing (default True)
    - delay (float): delay seconds before clearing
    """
    
    try:
        # Detect Jupyter environment
        from IPython import get_ipython
        ipython_shell = get_ipython()
        if ipython_shell is not None and "IPKernelApp" in ipython_shell.config:
            from IPython.display import clear_output
            clear_output(wait=wait)

    except Exception:
        # Fallback terminal clear on error
        if wait:
            time.sleep(delay)
            
        os.system('cls' if os.name == 'nt' else 'clear')