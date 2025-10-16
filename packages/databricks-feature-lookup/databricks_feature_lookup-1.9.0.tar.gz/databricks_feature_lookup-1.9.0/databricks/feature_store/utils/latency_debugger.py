from typing import Callable


class LatencyDebugger:
    def __init__(self, current_time_seconds_fn: Callable[[], float]):
        # list of tuples (tag, elapsed_time) in milliseconds
        self.enabled = False
        self.current_time_fn = current_time_seconds_fn
        self.elapsed_times = None

    def init(self):
        self.enabled = True
        self.elapsed_times = [("start", self._current_time_ms())]

    def add_latency(self, tag: str):
        if self.enabled:
            self.elapsed_times.append((tag, self._current_time_ms()))

    def debug_string(self) -> str:
        if not self.enabled:
            return ""
        start = self.elapsed_times[0][1]
        latencies = [(tag, t - start) for (tag, t) in self.elapsed_times]
        return f"Latency Debugger: {latencies}"

    def _current_time_ms(self):
        return int(self.current_time_fn() * 1000)
