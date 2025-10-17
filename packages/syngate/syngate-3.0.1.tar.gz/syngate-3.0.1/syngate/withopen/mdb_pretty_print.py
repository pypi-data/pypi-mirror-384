#import jupyter_max.pretty_print

#jupyter_max.pretty_print.position (text, position='center', width=None)
#jupyter_max.pretty_print.stylize (sentence, color=None, rgb=None, bold=False, underline=False, italic=False, highlights=None)

"""
Terminal Text Styling and Alignment Utility

This module provides two primary functionalities for enhancing console output:

1. Text Alignment (`position` function):
   - Description:
     Align text horizontally within the terminal window. Supports 'left', 'center', and 'right' alignment.
     Automatically detects terminal width if not provided.
   
   - When to use:
     Use this function when you want to display text aligned to left, center, or right in the console
     to improve readability or UI layout without relying on external libraries.

   - How to use:
     Call `position(text, position='center', width=None)`.
     - `text` (str): The string you want to align.
     - `position` (str): Alignment option; valid values are 'left', 'center', 'right'. Defaults to 'center'.
     - `width` (int, optional): Width in characters for alignment. If None, automatically uses terminal width.

   Example:
     position("Hello World!", position='right')

2. Styled and Highlighted Text Formatting (`stylize` function):
   - Description:
     Returns a string with ANSI escape codes to style text colors, fonts, and highlights.
     Supports 8-bit colors, 24-bit RGB colors, and text styles such as bold, underline, and italic.
     Allows styling entire sentences or specific highlighted substrings with different styles.

   - When to use:
     Use this function when you want to output colorful and styled text in the terminal,
     including highlighting certain words or phrases differently from the rest of the sentence.

   - How to use:
     Call `stylize(sentence, color=None, rgb=None, bold=False, underline=False, italic=False, highlights=None)`.
     - `sentence` (str): The full text to style.
     - `color` (str): Optional. Named color for entire sentence (e.g., 'red', 'green').
     - `rgb` (tuple): Optional. 24-bit color as (r, g, b).
     - `bold`, `underline`, `italic` (bool): Optional styles for entire sentence.
     - `highlights` (list of dict): Optional. List of substrings to highlight differently. Each dict can have:
         - 'text': substring to highlight (required),
         - 'color': color name (optional),
         - 'rgb': 24-bit color tuple (optional),
         - 'bold', 'underline', 'italic': booleans for styles (optional).

   Example:
     highlights = [
         {'text': 'error', 'color': 'red', 'bold': True},
         {'text': 'warning', 'color': 'yellow', 'underline': True}
     ]
     styled_str = stylize("This is an error and a warning message", highlights=highlights)
     print(styled_str)

Notes:
- ANSI styling may not render correctly on all terminal emulators.
- The italic style may not be supported everywhere.
- The alignment uses simple Python string methods and terminal width detection; some terminals may behave differently.
- The stylize function returns the styled string. Use print() to display it.
"""



import shutil

def position(text, position='center', width=None):
    """
    Align text horizontally within the terminal width and return it as a string.

    Args:
        text (str): The text to align.
        position (str): Alignment position, one of 'left', 'center', 'right'. Default is 'center'.
        width (int, optional): Width of the output. Defaults to terminal width if None.

    Returns:
        str: The aligned text string.
    """
    # Get terminal width if width not provided
    if width is None:
        width = shutil.get_terminal_size((80, 20)).columns

    if position == 'center':
        return text.center(width)
    elif position == 'left':
        return text.ljust(width)
    elif position == 'right':
        return text.rjust(width)
    else:
        return text  # default, no alignment


#-------------------------------------------------------------------------------------------------------------------------------------------


# Built-in ANSI color codes as string literals
COLORS = {
    "reset": "\033[0m",
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

# Style codes as string literals
STYLES = {
    "bold": "\033[1m",
    "underline": "\033[4m",
    "italic": "\033[3m",  # May not work in all terminals
    "reset": "\033[0m",
}

def style_text(text, color=None, rgb=None, bold=False, underline=False, italic=False):
    """
    Style text using ANSI escape codes with explicit "\033[...m" strings.

    Args:
        text (str): Text to style.
        color (str): Built-in color name.
        rgb (tuple): (r,g,b) tuple for 24-bit color.
        bold, underline, italic (bool): Styles.

    Returns:
        str: Styled text with ANSI escape sequences.
    """
    codes = []

    # 24-bit RGB color code
    if rgb:
        r, g, b = rgb
        codes.append(f"\033[38;2;{r};{g};{b}m")
    elif color and color in COLORS:
        codes.append(COLORS[color])

    if bold:
        codes.append(STYLES["bold"])
    if underline:
        codes.append(STYLES["underline"])
    if italic:
        codes.append(STYLES["italic"])

    start = "".join(codes)
    end = STYLES["reset"]
    return f"{start}{text}{end}"

def stylize (sentence, color=None, rgb=None, bold=False, underline=False, italic=False, highlights=None):
    """
    Return sentence with entire text styled or multiple highlighted parts as a string.

    Args:
        sentence (str): Sentence to style.
        color (str): Built-in color name for whole sentence.
        rgb (tuple): RGB tuple for whole sentence.
        bold, underline, italic (bool): Styles for whole sentence.
        highlights (list of dict): Each dict has:
            'text': substring,
            'color': built-in color name (optional),
            'rgb': RGB tuple (optional),
            'bold', 'underline', 'italic' (bool, optional).
    Returns:
        str: Styled string with ANSI codes.
    """
    if color or rgb or bold or underline or italic:
        return style_text(sentence, color=color, rgb=rgb, bold=bold, underline=underline, italic=italic)

    if not highlights:
        return sentence

    parts = []
    last_index = 0
    highlights_positions = []

    # Find first occurrence of each highlight substring
    for hl in highlights:
        start = sentence.find(hl['text'])
        if start != -1:
            highlights_positions.append((start, start + len(hl['text']), hl))

    # Sort highlights by start index
    highlights_positions.sort(key=lambda x: x[0])

    for start, end, hl in highlights_positions:
        if start >= last_index:
            # Append normal text before highlight
            parts.append(sentence[last_index:start])
            # Style the highlighted text part
            styled = style_text(
                sentence[start:end],
                color=hl.get('color'),
                rgb=hl.get('rgb'),
                bold=hl.get('bold', False),
                underline=hl.get('underline', False),
                italic=hl.get('italic', False)
            )
            parts.append(styled)
            last_index = end

    parts.append(sentence[last_index:])
    return "".join(parts)