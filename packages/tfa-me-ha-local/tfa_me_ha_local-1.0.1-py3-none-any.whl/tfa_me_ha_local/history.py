"""TFA.me library for Home Assistant: history.py"""

from collections import deque
from datetime import datetime



class SensorHistory:
    """Class to store a history, specially for rain sensor to calculate rain of last hour & last 24 hours)."""

    def __init__(self, max_age_minutes=60) -> None:
        """Initalaize history queue."""
        self.max_age = max_age_minutes * 60
        self.data: deque[tuple[float, int]] = deque()  # Stores (value, timestamp)

    def add_measurement(self, value, ts):
        """Add new value with time stamp."""
        ts_last = 0
        val_last = 0
        length = len(self.data)
        if length != 0:
            entry_last = self.data[-1]
            ts_last = entry_last[1]
            val_last = entry_last[0]
        if (ts_last != ts) & (val_last != value):
            self.data.append((value, ts))
            self.cleanup()

    def cleanup(self):
        """Remove entries older max_age seconds."""
        utc_now = datetime.now()
        utc_now_ts = int(utc_now.timestamp())
        run = 1
        while self.data and (run == 1):
            ts1 = int(self.data[0][1])
            ts2 = utc_now_ts - self.max_age
            if ts1 < ts2:
                self.data.popleft()
            else:
                run = 0

    def get_data(self):
        """Return list with values."""
        return list(self.data)

    def get_oldest_and_newest(self):
        """Return oldest and newest measuerement tuple."""
        if not self.data:
            return None, None  # If list is empty
        return self.data[0], self.data[-1]  # First(oldest) and last(newest) entry
