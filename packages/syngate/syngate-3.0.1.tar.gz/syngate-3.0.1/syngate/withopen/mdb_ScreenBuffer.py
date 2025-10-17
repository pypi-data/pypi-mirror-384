import os
from datetime import datetime
import threading
from .mdb_max_clear import wipe_screen # or replace with IPython.display.clear_output
import shutil

#def align_text(self, text, alignment=None):

def align_text(text, alignment=None):
    width = shutil.get_terminal_size().columns

    # Default to 'left' if alignment is None
    if alignment is None:
        alignment = 'left'

    # Convert numeric strings to integers
    if isinstance(alignment, str):
        alignment = alignment.strip()
        if alignment.lstrip('-').isdigit():
            alignment = int(alignment)

    # Handle integer-based alignment
    if isinstance(alignment, int):
        if alignment >= 0:
            return ' ' * alignment + text
        else:
            end_col = width + alignment
            start_col = max(0, end_col - len(text))
            return ' ' * start_col + text

    # Handle keyword alignment
    elif isinstance(alignment, str):
        alignment = alignment.lower()
        if alignment == 'left':
            return text
        elif alignment == 'center':
            return text.center(width)
        elif alignment == 'right':
            return text.rjust(width)

    # Fallback
    return text


class ScreenBuffer:
    EMOJI_STATES = {
        0: "🟢",
        1: "🟡",
        2: "🔴"
    }

    FILLER = "<<FILLER>>"

    def __init__(
        self,
        wait=True,
        log_file=None,
        max_main=None,
        max_wait=None,
        max_display=None,
        start=False,
        header=None,
        header_alignment=None,
        footer=None,              
        footer_alignment=None,  
        show_header=None,
        show_footer=None,
        silent_display=None,
        only_display=None,
        auto_clean_edges=False,
        auto_clean_silent_only_display=False,
        shift_max_display=True            
    ):
        self.buffer = []
        self.wait = wait
    
        self.silent_display = self._validate_silent_display(silent_display)
        self.only_display = self._validate_silent_display(only_display)
    
        self.max_main = max_main
        self.max_wait = max_wait
        self.max_display = max_display
        self.shift_max_display = shift_max_display
    
        self.auto_clean_edges = auto_clean_edges
        self.auto_clean_silent_only_display = auto_clean_silent_only_display
    
        if self.max_wait is not None and self.max_display is not None:
            if self.max_wait < self.max_display:
                raise ValueError("max_wait cannot be less than max_display")
    
        self.header = header if isinstance(header, str) else None
        self.footer = footer if isinstance(footer, str) else None
    
        self.show_header = show_header if show_header is not None else bool(self.header)
        self.show_footer = show_footer if show_footer is not None else bool(self.footer)
    
        self.header_alignment = header_alignment    
        self.footer_alignment = footer_alignment   
    
        self.buffer_lock = threading.RLock()
        self.file_lock = threading.RLock()
    
        if log_file:
            self.log_file = self._prepare_log_path(log_file)
            base, ext = os.path.splitext(self.log_file)
            self.wait_log_file = f"{base}_wait{ext}"
            self.header_file = f"{base}_header{ext}"
            self.footer_file = f"{base}_footer{ext}"
        else:
            self.log_file = None
            self.wait_log_file = None
            self.header_file = None
            self.footer_file = None
    
        if start:
            self._reset_all()
        self.refresh_buffer_from_wait_log()
    
        if not self.wait:
            self.display()
    
        self.alignments = {}  


    def _validate_silent_display(self, val):
        if val is None:
            return None
        if isinstance(val, int):
            return val
        if isinstance(val, list):
            for i in val:
                if not isinstance(i, int):
                    raise ValueError("silent_display list must contain integers")
            return val
        if isinstance(val, slice):
            return val
        if isinstance(val, str):
            if val.lower() == "all":
                return val.lower()
            raise ValueError("silent_display string must be 'all'")
        raise ValueError("Invalid silent_display value")

    def refresh_buffer_from_wait_log(self):
        if self.wait_log_file and os.path.exists(self.wait_log_file):
            try:
                with open(self.wait_log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip() and not self.buffer:
                    with self.buffer_lock:
                        self.buffer = content.splitlines()
            except Exception:
                pass

    def _reset_all(self):
        with self.buffer_lock:
            self.buffer.clear()
        if self.wait_log_file:
            try:
                with self.file_lock, open(self.wait_log_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if self.header_file:
            try:
                with self.file_lock, open(self.header_file, "w", encoding="utf-8") as f:
                    f.write(self.header if self.header is not None else "")
            except Exception:
                pass
        if self.footer_file:
            try:
                with self.file_lock, open(self.footer_file, "w", encoding="utf-8") as f:
                    f.write(self.footer if self.footer is not None else "")
            except Exception:
                pass

    def _prepare_log_path(self, filename):
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        filename = self._ensure_txt_extension(filename)
        return os.path.join(logs_dir, filename)

    def _ensure_txt_extension(self, path):
        return path if path.lower().endswith('.txt') else f"{path}.txt"


    def get_header(self):
        if not self.show_header or self.header is None:
            return ""
        header = ""
        if self.header_file and os.path.exists(self.header_file):
            try:
                with open(self.header_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    header = content if content else (self.header or "")
            except Exception:
                header = self.header or ""
        else:
            header = self.header or ""
    
        if self.header_alignment:
            try:
                header = align_text(header, self.header_alignment)
            except Exception:
                pass
    
        return header

    def set_header(self, new_header, save_to_file=True):
        self.header = new_header if isinstance(new_header, str) else None
        if save_to_file and self.header_file:
            try:
                with open(self.header_file, "w", encoding="utf-8") as f:
                    f.write(self.header if self.header is not None else "")
            except Exception:
                pass
        if self.header:
            self.show_header = True


    def flush(self):
        wipe_screen(wait=True)

    def update(self, **kwargs):
        # === Handle silent_display and only_display exclusivity ===
        new_silent = kwargs.get("silent_display", None)
        new_only = kwargs.get("only_display", None)
        if new_silent is not None and new_only is not None:
            raise ValueError("silent_display and only_display cannot be used simultaneously")

        # === Preprocessing for validation ===
        for key in ["silent_display", "only_display"]:
            if key in kwargs:
                kwargs[key] = self._validate_silent_display(kwargs[key])

        for key, value in kwargs.items():
            if key == "header":
                self.set_header(value, save_to_file=True)
            elif key == "footer":
                self.set_footer(value, save_to_file=True)
            elif key == "show_header":
                self.show_header = bool(value)
            elif key == "show_footer":
                self.show_footer = bool(value)
            elif key == "silent_display":
                self.silent_display = value
                self.only_display = None
            elif key == "only_display":
                self.only_display = value
                self.silent_display = None
            elif key == "log_file":
                # Recreate log file paths
                self.log_file = self._prepare_log_path(value)
                base, ext = os.path.splitext(self.log_file)
                self.wait_log_file = f"{base}_wait{ext}"
                self.header_file = f"{base}_header{ext}"
                self.footer_file = f"{base}_footer{ext}"
            elif key in {
                "wait", "max_main", "max_wait", "max_display",
                "shift_max_display", "auto_clean_edges", "auto_clean_silent_only_display"
            }:
                setattr(self, key, value)
            else:
                if hasattr(self, key):
                    setattr(self, key, value)

        if self.max_wait is not None and self.max_display is not None:
            if self.max_wait < self.max_display:
                raise ValueError("max_wait cannot be less than max_display")

        if not self.wait:
            self.display()

    def delete(self, index, contains=None, exact=True):
        with self.buffer_lock:
            if not (isinstance(index, int) or isinstance(index, slice)):
                raise TypeError("Index must be int or slice")

            def line_matches(line):
                if contains is None:
                    return True
                line_lower = line.lower()
                contains_lower = contains.lower()
                if exact:
                    words = line_lower.split()
                    return contains_lower in words
                else:
                    return contains_lower in line_lower

            if isinstance(index, int):
                if index < 0:
                    index += len(self.buffer)
                if not (0 <= index < len(self.buffer)):
                    raise IndexError("Index out of range")
                if line_matches(self.buffer[index]):
                    self.buffer.pop(index)
                    self.alignments.pop(index, None)  # Remove alignment tag
            else:
                indices = list(range(*index.indices(len(self.buffer))))
                new_buffer = []
                new_alignments = {}
                for i, line in enumerate(self.buffer):
                    if i in indices and line_matches(line):
                        continue
                    new_buffer.append(line)
                    if i in self.alignments:
                        new_alignments[len(new_buffer) - 1] = self.alignments[i]
                self.buffer = new_buffer
                self.alignments = new_alignments

        if not self.wait:
            self.display()

    def _trim_wait_log_file(self):
        if not self.wait_log_file or self.max_wait is None:
            return
        try:
            with self.file_lock, open(self.wait_log_file, "r+", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) > self.max_wait:
                    lines = lines[-self.max_wait:]
                    f.seek(0)
                    f.truncate()
                    f.writelines(lines)
        except Exception:
            pass

    def clear(self):
        with self.buffer_lock:
            self.buffer.clear()
            self.alignments.clear()
        if self.wait_log_file:
            try:
                with self.file_lock, open(self.wait_log_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if not self.wait:
            self.display()

    def clear_all(self):
        with self.buffer_lock:
            self.buffer.clear()
            self.alignments.clear()
        self.header = None
        self.footer = None
        self.show_header = False
        self.show_footer = False
        if self.wait_log_file:
            try:
                with self.file_lock, open(self.wait_log_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if self.header_file:
            try:
                with self.file_lock, open(self.header_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if self.footer_file:
            try:
                with self.file_lock, open(self.footer_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if not self.wait:
            self.display()

        if not self.wait:
            self.display()

    def get_footer(self):
        if not self.show_footer or self.footer is None:
            return ""
        footer = ""
        if self.footer_file and os.path.exists(self.footer_file):
            try:
                with open(self.footer_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    footer = content if content else (self.footer or "")
            except Exception:
                footer = self.footer or ""
        else:
            footer = self.footer or ""
    
        if self.footer_alignment:
            try:
                footer = align_text(footer, self.footer_alignment)
            except Exception:
                pass
    
        return footer

    def set_footer(self, new_footer, save_to_file=True):
        self.footer = new_footer if isinstance(new_footer, str) else None
        if save_to_file and self.footer_file:
            try:
                with open(self.footer_file, "w", encoding="utf-8") as f:
                    f.write(self.footer if self.footer is not None else "")
            except Exception:
                pass
        if self.footer:
            self.show_footer = True
        if not self.wait:
            self.display()

    def put(self, text, state=0, index=None, fill_value=None, alignment=None):
        if not self.buffer:
            self.refresh_buffer_from_wait_log()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        emoji = self.EMOJI_STATES.get(state, "🟢")

        if not isinstance(text, str):
            text = str(text)

        fill_value = self.FILLER if fill_value is None else fill_value

        with self.buffer_lock:
            if index is None:
                index = len(self.buffer)
                self.buffer.append(text)
            else:
                if index < 0:
                    index += len(self.buffer)
                if index < 0:
                    raise IndexError("Negative index out of range after adjustment")
                if index >= len(self.buffer):
                    self.buffer.extend([fill_value] * (index - len(self.buffer)))
                    self.buffer.append(text)
                else:
                    self.buffer[index] = text

            if alignment is not None:
                self.alignments[index] = alignment

        if self.wait_log_file:
            try:
                with self.file_lock, open(self.wait_log_file, "w", encoding="utf-8") as f:
                    with self.buffer_lock:
                        aligned_lines = []
                        for i, line in enumerate(self.buffer):
                            if line == self.FILLER:
                                aligned_lines.append("")
                            else:
                                align = self.alignments.get(i, 'left')
                                aligned_lines.append(align_text(line, align))
                        f.write("\n".join(aligned_lines) + "\n")
                self._trim_wait_log_file()
            except Exception:
                pass

        if self.log_file:
            try:
                with self.file_lock:
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        log_line = f"{now} {emoji} {text}"
                        if index is not None:
                            f.write(f"{log_line} [📍{index}]\n")
                        else:
                            f.write(f"{log_line}\n")
                if self.max_main is not None:
                    try:
                        with self.file_lock, open(self.log_file, "r+", encoding="utf-8") as f:
                            lines = f.readlines()
                            if len(lines) > self.max_main:
                                lines = lines[-self.max_main:]
                                f.seek(0)
                                f.truncate()
                                f.writelines(lines)
                    except Exception:
                        pass
            except Exception as e:
                raise RuntimeError(f"Error writing to log file: {e}")

        if not self.wait:
            self.display()

    def format_text_for_display(self):
        header = self.get_header()
        footer = self.get_footer()
    
        with self.buffer_lock:
            full_buffer = list(self.buffer)
    
            # === NEW: Snapshot of text-alignment pairs before any filtering ===
            indexed_buffer = [
                [line if line != self.FILLER else "", self.alignments.get(i, 'left')]
                for i, line in enumerate(full_buffer)
            ]
    
        total_len = len(indexed_buffer)
    
        # === Step 1: Determine display range ===
        if self.max_display is not None:
            if self.shift_max_display:
                display_start = 0
                display_end = total_len
            else:
                display_start = max(total_len - self.max_display, 0)
                display_end = total_len
        else:
            display_start = 0
            display_end = total_len
    
        self.display_range = (display_start, display_end)
    
        active_buffer = [indexed_buffer[i][0] for i in range(display_start, display_end)]
        active_alignments = [indexed_buffer[i][1] for i in range(display_start, display_end)]
        visible_indices = list(range(display_start, display_end))
        active_len = len(active_buffer)
    
        # === Step 2: Apply only_display or silent_display ===
        if self.only_display is not None:
            try:
                if isinstance(self.only_display, str) and self.only_display.lower() == 'all':
                    pass
                else:
                    selected = set()
                    if isinstance(self.only_display, list):
                        selected = set(self.only_display)
                    elif isinstance(self.only_display, int):
                        selected = {self.only_display}
                    elif isinstance(self.only_display, slice):
                        selected = set(range(len(full_buffer))[self.only_display])
    
                    active_buffer = [
                        active_buffer[i] if visible_indices[i] in selected else ""
                        for i in range(active_len)
                    ]
                    active_alignments = [
                        active_alignments[i] if visible_indices[i] in selected else 'left'
                        for i in range(active_len)
                    ]
            except Exception:
                active_buffer = []
                active_alignments = []
    
        elif self.silent_display is not None:
            try:
                if isinstance(self.silent_display, str) and self.silent_display.lower() == 'all':
                    active_buffer = [""] * active_len
                    active_alignments = ["left"] * active_len
                else:
                    muted = set()
                    if isinstance(self.silent_display, list):
                        muted = set(self.silent_display)
                    elif isinstance(self.silent_display, int):
                        muted = {self.silent_display}
                    elif isinstance(self.silent_display, slice):
                        muted = set(range(len(full_buffer))[self.silent_display])
    
                    active_buffer = [
                        "" if visible_indices[i] in muted else active_buffer[i]
                        for i in range(active_len)
                    ]
                    active_alignments = [
                        "left" if visible_indices[i] in muted else active_alignments[i]
                        for i in range(active_len)
                    ]
            except Exception:
                active_buffer = []
                active_alignments = []
    
        # ✅ Fix: Realign visible_indices to match active_buffer length
        visible_indices = visible_indices[:len(active_buffer)]
        active_alignments = active_alignments[:len(active_buffer)]
    
        # === Step 3: Clean silent/only_display lines ===
        if self.auto_clean_silent_only_display:
            clean_buffer = []
            clean_alignments = []
            clean_indices = []
            for i, line in enumerate(active_buffer):
                if line.strip() != "":
                    clean_buffer.append(line)
                    clean_alignments.append(active_alignments[i])
                    clean_indices.append(visible_indices[i])
            active_buffer = clean_buffer
            active_alignments = clean_alignments
            visible_indices = clean_indices
    
        # === Step 4: Enforce max_display again if needed ===
        if self.max_display is not None:
            active_buffer = active_buffer[-self.max_display:]
            active_alignments = active_alignments[-len(active_buffer):]
            visible_indices = visible_indices[-len(active_buffer):]
    
        # === Step 5: Edge trimming ===
        if self.auto_clean_edges:
            while active_buffer and active_buffer[0].strip() == "":
                active_buffer.pop(0)
                active_alignments.pop(0)
                visible_indices.pop(0)
            while active_buffer and active_buffer[-1].strip() == "":
                active_buffer.pop()
                active_alignments.pop()
                visible_indices.pop()
            if active_buffer:
                active_buffer.insert(0, "")
                active_alignments.insert(0, 'left')
                visible_indices.insert(0, -1)
                active_buffer.append("")
                active_alignments.append('left')
                visible_indices.append(-1)
    
        # === Step 6: Collect with alignment (No formatting) ===
        rendered = []
        for text, align in zip(active_buffer, active_alignments):
            rendered.append([text, align])
    
        # === Step 7: Return list of [text, alignment] pairs ===
        result = []
    
        if self.show_header and header:
            result.append([header.rstrip("\n"), self.header_alignment or 'left'])
    
        result.extend(rendered)
    
        if self.show_footer and footer:
            result.append([footer.lstrip("\n"), self.footer_alignment or 'left'])
    
        return result

    def get_text(self):
        # Use format_text_for_display to get structured text with alignments
        formatted = self.format_text_for_display()
        
        # Apply alignment to each line before joining
        lines = [align_text(text, alignment) for text, alignment in formatted]
        
        return "\n".join(lines)

    def display(self):
        wipe_screen(wait=True)
        lines = self.format_text_for_display()
        for text, alignment in lines:
            if alignment:
                print(align_text(text, alignment))
            else:
                print(text)

    def display_index(self):
        with self.buffer_lock:
            for i, line in enumerate(self.buffer):
                print(f"[{i}]: {repr(line)}")

    def flush(self):
        wipe_screen(wait=True)

    def update(self, **kwargs):
        # === Handle silent_display and only_display exclusivity ===
        new_silent = kwargs.get("silent_display", None)
        new_only = kwargs.get("only_display", None)
        if new_silent is not None and new_only is not None:
            raise ValueError("silent_display and only_display cannot be used simultaneously")

        # === Preprocessing for validation ===
        for key in ["silent_display", "only_display"]:
            if key in kwargs:
                kwargs[key] = self._validate_silent_display(kwargs[key])

        for key, value in kwargs.items():
            if key == "header":
                self.set_header(value, save_to_file=True)
            elif key == "footer":
                self.set_footer(value, save_to_file=True)
            elif key == "show_header":
                self.show_header = bool(value)
            elif key == "show_footer":
                self.show_footer = bool(value)
            elif key == "silent_display":
                self.silent_display = value
                self.only_display = None
            elif key == "only_display":
                self.only_display = value
                self.silent_display = None
            elif key == "log_file":
                # Recreate log file paths
                self.log_file = self._prepare_log_path(value)
                base, ext = os.path.splitext(self.log_file)
                self.wait_log_file = f"{base}_wait{ext}"
                self.header_file = f"{base}_header{ext}"
                self.footer_file = f"{base}_footer{ext}"
            elif key in {
                "wait", "max_main", "max_wait", "max_display",
                "shift_max_display", "auto_clean_edges", "auto_clean_silent_only_display"
            }:
                setattr(self, key, value)
            elif key == "header_alignment":
                self.header_alignment = value
            elif key == "footer_alignment":
                self.footer_alignment = value
            else:
                if hasattr(self, key):
                    setattr(self, key, value)

        if self.max_wait is not None and self.max_display is not None:
            if self.max_wait < self.max_display:
                raise ValueError("max_wait cannot be less than max_display")

        if not self.wait:
            self.display()

    def delete(self, index, contains=None, exact=True):
        with self.buffer_lock:
            if not (isinstance(index, int) or isinstance(index, slice)):
                raise TypeError("Index must be int or slice")

            def line_matches(line):
                if contains is None:
                    return True
                line_lower = line.lower()
                contains_lower = contains.lower()
                if exact:
                    words = line_lower.split()
                    return contains_lower in words
                else:
                    return contains_lower in line_lower

            if isinstance(index, int):
                if index < 0:
                    index += len(self.buffer)
                if not (0 <= index < len(self.buffer)):
                    raise IndexError("Index out of range")
                if line_matches(self.buffer[index]):
                    self.buffer.pop(index)
                    self.alignments.pop(index, None)  # Remove alignment tag
            else:
                indices = list(range(*index.indices(len(self.buffer))))
                new_buffer = []
                new_alignments = {}
                for i, line in enumerate(self.buffer):
                    if i in indices and line_matches(line):
                        continue
                    new_buffer.append(line)
                    if i in self.alignments:
                        new_alignments[len(new_buffer) - 1] = self.alignments[i]
                self.buffer = new_buffer
                self.alignments = new_alignments

        if not self.wait:
            self.display()

    def _trim_wait_log_file(self):
        if not self.wait_log_file or self.max_wait is None:
            return
        try:
            with self.file_lock, open(self.wait_log_file, "r+", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) > self.max_wait:
                    lines = lines[-self.max_wait:]
                    f.seek(0)
                    f.truncate()
                    f.writelines(lines)
        except Exception:
            pass

    def clear(self):
        with self.buffer_lock:
            self.buffer.clear()
            self.alignments.clear()
        if self.wait_log_file:
            try:
                with self.file_lock, open(self.wait_log_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if not self.wait:
            self.display()

    def clear_all(self):
        with self.buffer_lock:
            self.buffer.clear()
            self.alignments.clear()
        self.header = None
        self.footer = None
        self.show_header = False
        self.show_footer = False
        if self.wait_log_file:
            try:
                with self.file_lock, open(self.wait_log_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if self.header_file:
            try:
                with self.file_lock, open(self.header_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if self.footer_file:
            try:
                with self.file_lock, open(self.footer_file, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        if not self.wait:
            self.display()


    def return_screen(self, func, *args, **kwargs):
        screen = kwargs.get("screen", None)
        try:
            result = func(*args, **kwargs)

            if isinstance(result, ScreenBuffer):
                return (result,)

            if isinstance(result, tuple):
                if any(isinstance(x, ScreenBuffer) for x in result):
                    filtered = [x for x in result if not isinstance(x, ScreenBuffer)]
                    screens = [x for x in result if isinstance(x, ScreenBuffer)]
                    screen = screens[0]
                    return (screen, *filtered)
                else:
                    if screen is None:
                        screen = self
                    return (screen, *result)

            if screen is None:
                screen = self
            return (screen, result)

        except Exception as e:
            if screen is None:
                screen = self
            screen.put(f"[ERROR] {e}", state=2)
            return (screen, None)
