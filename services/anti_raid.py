from __future__ import annotations

import datetime as dt
from collections import deque


class RaidDetector:
    def __init__(self, threshold: int = 10, seconds: int = 60, alert_cooldown_seconds: int = 120) -> None:
        self.threshold = threshold
        self.seconds = seconds
        self.alert_cooldown_seconds = alert_cooldown_seconds
        self.events: deque[dt.datetime] = deque()
        self.last_alert_at: dt.datetime | None = None

    def record_join(self) -> bool:
        now = dt.datetime.now(dt.timezone.utc)
        self.events.append(now)
        while self.events and (now - self.events[0]).total_seconds() > self.seconds:
            self.events.popleft()
        if len(self.events) < self.threshold:
            return False
        if self.last_alert_at and (now - self.last_alert_at).total_seconds() < self.alert_cooldown_seconds:
            return False
        self.last_alert_at = now
        return True
