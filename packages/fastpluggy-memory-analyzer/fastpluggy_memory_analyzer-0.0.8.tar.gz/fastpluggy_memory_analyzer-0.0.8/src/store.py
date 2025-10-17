import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Sample:
    ts: float
    method: str
    endpoint: str
    duration_s: float
    delta_bytes: int
    top_types: Optional[List[dict]] = None  # [{type, count_delta, size_delta, avg_size}]


@dataclass
class EndpointStats:
    samples: int = 0
    bytes_delta_sum: int = 0
    durations_sum: float = 0.0
    recent: deque = field(default_factory=lambda: deque(maxlen=50))

    def add(self, s: Sample):
        self.samples += 1
        self.bytes_delta_sum += s.delta_bytes
        self.durations_sum += s.duration_s
        self.recent.appendleft(s)

    @property
    def avg_delta(self) -> float:
        return self.bytes_delta_sum / self.samples if self.samples else 0.0

    @property
    def avg_duration(self) -> float:
        return self.durations_sum / self.samples if self.samples else 0.0


class MemoryStore:
    def __init__(self):
        self._lock = threading.RLock()
        self._by_endpoint: Dict[Tuple[str, str], EndpointStats] = defaultdict(EndpointStats)
        self._last_diff_top: List[dict] = []
        # Runtime configuration that can be toggled via UI
        self._monitor_all_endpoints = False

    def record(self, s: Sample):
        key = (s.method, s.endpoint)
        with self._lock:
            self._by_endpoint[key].add(s)
            if s.top_types:
                self._last_diff_top = s.top_types

    def snapshot(self):
        with self._lock:
            data = []
            for (m, e), st in self._by_endpoint.items():
                data.append({
                    "method": m,
                    "endpoint": e,
                    "samples": st.samples,
                    "avg_delta": st.avg_delta,
                    "avg_duration": st.avg_duration,
                    "recent": list(st.recent),
                })
            data.sort(key=lambda x: x["avg_delta"], reverse=True)
            return data

    def get(self, method: str, endpoint: str) -> Optional[EndpointStats]:
        with self._lock:
            return self._by_endpoint.get((method, endpoint))

    def last_diff_top(self) -> List[dict]:
        with self._lock:
            return list(self._last_diff_top)

    def get_monitor_all_endpoints(self) -> bool:
        """Get the current state of monitor_all_endpoints setting."""
        with self._lock:
            return self._monitor_all_endpoints

    def set_monitor_all_endpoints(self, enabled: bool) -> bool:
        """Set the monitor_all_endpoints setting and return the new state."""
        with self._lock:
            self._monitor_all_endpoints = enabled
            return self._monitor_all_endpoints

    def toggle_monitor_all_endpoints(self) -> bool:
        """Toggle the monitor_all_endpoints setting and return the new state."""
        with self._lock:
            self._monitor_all_endpoints = not self._monitor_all_endpoints
            return self._monitor_all_endpoints


store = MemoryStore()
