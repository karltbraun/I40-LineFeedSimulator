from __future__ import annotations

import time
from collections import deque


class SpeedTracker:
    """Maintains rolling speed averages for 1-min, 5-min, and full-run windows."""

    def __init__(self) -> None:
        self._1min: deque[tuple[float, float]] = deque()
        self._5min: deque[tuple[float, float]] = deque()
        self._run: deque[tuple[float, float]] = deque()

    def reset(self) -> None:
        self._1min.clear()
        self._5min.clear()
        self._run.clear()

    def add(self, speed: float) -> None:
        now = time.monotonic()
        entry = (now, speed)
        self._1min.append(entry)
        self._5min.append(entry)
        self._run.append(entry)
        self._evict(self._1min, 60.0)
        self._evict(self._5min, 300.0)

    @staticmethod
    def _evict(dq: deque[tuple[float, float]], window: float) -> None:
        cutoff = time.monotonic() - window
        while dq and dq[0][0] < cutoff:
            dq.popleft()

    @staticmethod
    def _mean(dq: deque[tuple[float, float]]) -> float:
        if not dq:
            return 0.0
        return sum(v for _, v in dq) / len(dq)

    @property
    def avg_1min(self) -> float:
        self._evict(self._1min, 60.0)
        return self._mean(self._1min)

    @property
    def avg_5min(self) -> float:
        self._evict(self._5min, 300.0)
        return self._mean(self._5min)

    @property
    def avg_run(self) -> float:
        return self._mean(self._run)
