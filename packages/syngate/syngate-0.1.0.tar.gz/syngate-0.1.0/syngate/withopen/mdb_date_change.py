from datetime import datetime
from . import mdb_core as core

def get(txt_name, date_type, time_gap=1, day_start_hour=0):
    from datetime import datetime, timedelta, timezone

    # Get current UTC time (timezone-aware)
    now = datetime.now(timezone.utc)
    readable_now = now.strftime("%Y %m %d %H %M %S")

    try:
        prev_str = core.read_txt(txt_name)[0].strip()
        # Parse and set timezone to UTC
        prev_time = datetime.strptime(prev_str, "%Y %m %d %H %M %S").replace(tzinfo=timezone.utc)
    except (IndexError, ValueError, TypeError):
        core.write_all_files(readable_now, txt_name, txt_name, single_write=True, hide=True)
        return 'A'

    # Time unit to seconds mapping
    time_type_map = {
        's': 1, 'second': 1,
        'm': 60, 'min': 60, 'minute': 60,
        'h': 3600, 'hour': 3600,
        'd': 86400, 'day': 86400,
        'mo': 2592000, 'month': 2592000,
        'y': 31536000, 'year': 31536000
    }

    unit = date_type.lower()
    gap_seconds = time_type_map.get(unit)
    if gap_seconds is None:
        return "Invalid date_type. Use 's', 'm', 'h', 'd', 'mo', or 'y'."

    # --------- DATE-BASED UNITS ---------
    if unit in ['d', 'day']:
        def get_day_start(dt):
            return datetime(dt.year, dt.month, dt.day, hour=day_start_hour, tzinfo=timezone.utc)

        now_start = get_day_start(now)
        prev_start = get_day_start(prev_time)

        if now_start > prev_start:
            core.write_all_files(readable_now, txt_name, txt_name, single_write=True, hide=True)
            return 'A'
        else:
            return 'R'

    elif unit in ['mo', 'month']:
        if (now.year != prev_time.year) or (now.month != prev_time.month):
            if now.day > 1 or now.hour >= day_start_hour:
                core.write_all_files(readable_now, txt_name, txt_name, single_write=True, hide=True)
                return 'A'
        return 'R'

    elif unit in ['y', 'year']:
        if now.year != prev_time.year:
            if now.month > 1 or now.day > 1 or now.hour >= day_start_hour:
                core.write_all_files(readable_now, txt_name, txt_name, single_write=True, hide=True)
                return 'A'
        return 'R'

    # --------- TIME-BASED UNITS (s, m, h) ---------
    delta_seconds = (now - prev_time).total_seconds()
    if delta_seconds >= gap_seconds * time_gap:
        #core.normal_write_file(txt_name, readable_now)
        core.write_all_files(readable_now, txt_name, txt_name, single_write=True, hide=True)
        return 'A'
    else:
        return 'R'
