import random
import time
from typing import Callable

from fastapi import Request
from pympler import muppy, summary
from starlette.middleware.base import BaseHTTPMiddleware

from .store import Sample, store


def _snapshot_summary():
    objs = muppy.get_objects()
    return summary.summarize(objs)


def _diff_bytes(a, b):
    try:
        diff = summary.get_diff(a, b)
    except Exception:
        return 0
    total = 0
    for row in diff or []:
        try:
            if isinstance(row, (list, tuple)):
                if len(row) >= 3:
                    total += int(row[2] or 0)
            else:
                total += int(getattr(row, "size", 0) or 0)
        except Exception:
            pass
    return total


def _row_to_dict(row):
    t = "unknown"; c = 0; s = 0; a = 0
    try:
        if isinstance(row, (list, tuple)):
            if len(row) > 0: t = row[0]
            if len(row) > 1: c = int(row[1] or 0)
            if len(row) > 2: s = int(row[2] or 0)
            if len(row) > 3: a = int(row[3] or 0)
            else: a = int(s // c) if c else 0
        else:
            t = getattr(row, "type", t)
            c = int(getattr(row, "count", 0) or 0)
            s = int(getattr(row, "size", 0) or 0)
            a = int(getattr(row, "avg", (s // c) if c else 0) or 0)
    except Exception:
        pass
    return {"type": t, "count_delta": c, "size_delta": s, "avg_size": a}


def _top_types_diff(a, b, limit=15):
    try:
        diff = summary.get_diff(a, b)
    except Exception:
        return []
    def size_of(row):
        try:
            if isinstance(row, (list, tuple)) and len(row) >= 3:
                return int(row[2] or 0)
            return int(getattr(row, "size", 0) or 0)
        except Exception:
            return 0
    diff_sorted = sorted(diff or [], key=size_of, reverse=True)[:limit]
    out = []
    for row in diff_sorted:
        rd = _row_to_dict(row)
        if rd["size_delta"] > 0:
            out.append(rd)
    return out


class PymplerAttributionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, sampling_rate: float = 0.1, debug_header: str = "X-Debug-Mem", monitor_all_endpoints: bool = False):
        super().__init__(app)
        self.sampling_rate = max(0.0, min(1.0, sampling_rate))
        self.debug_header = debug_header
        self.monitor_all_endpoints = monitor_all_endpoints

    async def dispatch(self, request: Request, call_next: Callable):
        force = request.headers.get(self.debug_header) in ("1", "true", "True", "yes")
        # Check dynamic setting from store as well as static setting
        dynamic_monitor_all = store.get_monitor_all_endpoints()
        do_sample = self.monitor_all_endpoints or dynamic_monitor_all or force or (random.random() < self.sampling_rate)

        route = request.scope.get("route")
        path_tpl = getattr(route, "path_format", request.url.path)
        method = request.method

        if not do_sample:
            response = await call_next(request)
            return response

        snap_before = _snapshot_summary()
        t0 = time.time()
        try:
            response = await call_next(request)
            return response
        finally:
            snap_after = _snapshot_summary()
            delta_bytes = _diff_bytes(snap_before, snap_after)
            top_types = _top_types_diff(snap_before, snap_after)

            sample = Sample(
                ts=time.time(),
                method=method,
                endpoint=path_tpl,
                duration_s=time.time() - t0,
                delta_bytes=int(delta_bytes),
                top_types=top_types,
            )
            store.record(sample)
