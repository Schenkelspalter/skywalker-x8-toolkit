"""Rolling statistics for decoded telemetry frames."""

from collections import deque
from dataclasses import dataclass
from statistics import mean
import time

from .frame import ZTWMantisFrame


@dataclass(frozen=True)
class ValueStats:
    average: float
    minimum: float
    maximum: float


class RollingFrameStatistics:
    def __init__(self, window_seconds: float = 2.0) -> None:
        self.window_seconds = window_seconds
        self._frames: deque[tuple[float, ZTWMantisFrame]] = deque()

    def add(self, frame: ZTWMantisFrame) -> None:
        now = time.time()
        self._frames.append((now, frame))
        self._trim(now)

    def _trim(self, now: float) -> None:
        while self._frames and now - self._frames[0][0] > self.window_seconds:
            self._frames.popleft()

    @property
    def sample_count(self) -> int:
        return len(self._frames)

    @property
    def time_span_s(self) -> float:
        if len(self._frames) < 2:
            return 0.0
        return self._frames[-1][0] - self._frames[0][0]

    def _stats(self, values: list[float]) -> ValueStats:
        return ValueStats(mean(values), min(values), max(values))

    @property
    def voltage(self) -> ValueStats:
        return self._stats([f.voltage_v for _, f in self._frames])

    @property
    def current(self) -> ValueStats:
        return self._stats([f.current_a for _, f in self._frames])

    @property
    def rpm_mechanical(self) -> ValueStats:
        return self._stats([f.rpm_mechanical for _, f in self._frames])

    @property
    def throttle_input(self) -> ValueStats:
        return self._stats([f.throttle_input_pct for _, f in self._frames])

    @property
    def throttle_output(self) -> ValueStats:
        return self._stats([f.throttle_output_pct for _, f in self._frames])

    @property
    def latest(self) -> ZTWMantisFrame | None:
        if not self._frames:
            return None
        return self._frames[-1][1]