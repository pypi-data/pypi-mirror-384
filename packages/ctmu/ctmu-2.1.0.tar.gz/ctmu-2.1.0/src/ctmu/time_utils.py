"""Time and date utilities"""

import time
from datetime import datetime, timezone
import calendar

def timestamp_to_date(timestamp, format='%Y-%m-%d %H:%M:%S'):
    """Convert timestamp to readable date"""
    try:
        dt = datetime.fromtimestamp(float(timestamp))
        return dt.strftime(format)
    except Exception as e:
        return f"Error: {e}"

def date_to_timestamp(date_str, format='%Y-%m-%d %H:%M:%S'):
    """Convert date string to timestamp"""
    try:
        dt = datetime.strptime(date_str, format)
        return int(dt.timestamp())
    except Exception as e:
        return f"Error: {e}"

def current_time(timezone_name=None, format='%Y-%m-%d %H:%M:%S'):
    """Get current time"""
    try:
        if timezone_name:
            import pytz
            tz = pytz.timezone(timezone_name)
            dt = datetime.now(tz)
        else:
            dt = datetime.now()
        return dt.strftime(format)
    except Exception as e:
        return datetime.now().strftime(format)

def time_diff(start_time, end_time, format='%Y-%m-%d %H:%M:%S'):
    """Calculate time difference"""
    try:
        start_dt = datetime.strptime(start_time, format)
        end_dt = datetime.strptime(end_time, format)
        diff = end_dt - start_dt
        
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"
    except Exception as e:
        return f"Error: {e}"

def stopwatch():
    """Simple stopwatch"""
    start = time.time()
    input("Press Enter to stop...")
    elapsed = time.time() - start
    return f"Elapsed: {elapsed:.2f} seconds"

def countdown(seconds):
    """Countdown timer"""
    try:
        seconds = int(seconds)
        while seconds > 0:
            mins, secs = divmod(seconds, 60)
            print(f"\r{mins:02d}:{secs:02d}", end='', flush=True)
            time.sleep(1)
            seconds -= 1
        return "\nTime's up!"
    except KeyboardInterrupt:
        return "\nCountdown stopped"
    except Exception as e:
        return f"Error: {e}"