import psutil
import sys
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastpluggy.core.auth import require_authentication
from fastpluggy.core.dependency import get_view_builder, get_fastpluggy
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.widgets import ButtonListWidget, AutoLinkWidget, CustomTemplateWidget
from pympler import muppy, summary

from ..widgets.psutil_analyzer import PsutilAnalyzerWidget

# Create router with authentication
psutil_analyzer_router = APIRouter(
    prefix="/psutil-analyzer",
    tags=["debug", "psutil"],
    dependencies=[Depends(require_authentication)],
)

@menu_entry(label="PSUtil Analyzer")
@psutil_analyzer_router.get("/", name="psutil_analyzer_dashboard")
async def psutil_analyzer_dashboard(
    request: Request,
    view_builder=Depends(get_view_builder),
    fast_pluggy=Depends(get_fastpluggy)
):
    """
    Render the PSUtil Analyzer dashboard using the custom widget.
    """
    # Register the widget if not already registered
    #available_widgets = fast_pluggy.get_global('available_widget', {})
    #if PsutilAnalyzerWidget.widget_type not in available_widgets:
    #    from fastpluggy_plugin.website_builder.src.widgets import get_class_path
    #    available_widgets[PsutilAnalyzerWidget.widget_type] = get_class_path(PsutilAnalyzerWidget)
    #    fast_pluggy.set_global('available_widget', available_widgets)
    
    # Generate the view with the PSUtil Analyzer widget
    return view_builder.generate(
        request,
        title="PSUtil Memory Analysis Dashboard",
        widgets=[
            PsutilAnalyzerWidget(
                title="PSUtil Memory Analysis Dashboard"
            ),
            ButtonListWidget(buttons=[
                AutoLinkWidget(label="Back to Debug Tools", route_name="list_tools"),
            ]),
        ]
    )


@psutil_analyzer_router.get("/current", name="current_heap")
async def current_heap(request: Request, limit: int = 50, view_builder=Depends(get_view_builder)):
    """Analyze current heap memory using pympler and psutil."""
    objs = muppy.get_objects()
    summ = summary.summarize(objs)
    summ_sorted = sorted(summ, key=lambda r: r[2], reverse=True)[: max(1, min(500, limit))]
    rows = []
    for r in summ_sorted:
        # Handle cases where pympler summary rows may not have all 4 elements
        row_data = {
            "type": r[0] if len(r) > 0 else "unknown",
            "count": r[1] if len(r) > 1 else 0,
            "size": r[2] if len(r) > 2 else 0,
            "avg": r[3] if len(r) > 3 else (r[2] // r[1] if len(r) > 1 and r[1] > 0 else 0)
        }
        rows.append(row_data)

    proc = psutil.Process()
    mi = proc.memory_full_info()

    context = {
        "rows": rows,
        "rss": mi.rss,
        "uss": getattr(mi, "uss", None),
        "pss": getattr(mi, "pss", None),
    }

    return view_builder.generate(
        request,
        title="Current Heap",
        widgets=[
            CustomTemplateWidget(
                template_name="memory_analyzer/memory_current.html.j2",
                context=context
            )
        ]
    )



@psutil_analyzer_router.get("/thread/{tid}", name="thread_detail")
async def thread_detail(tid: int, request: Request, fast_pluggy=Depends(get_fastpluggy)):
    """Return extended details for a given thread id if available.

    Adds Linux /proc-derived per-thread details when accessible. Also maps the
    OS native thread id (tid) to the Python threading name when available
    (py_name).
    """
    import os
    import threading

    proc = psutil.Process()
    try:
        tids = [t.id for t in proc.threads()]
    except Exception:
        tids = []
    if tid not in tids:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Build a map from native thread id -> Python thread name
    try:
        tid_to_pyname = {t.native_id: t.name for t in threading.enumerate() if t.native_id is not None}
    except Exception:
        tid_to_pyname = {}

    info = {
        "tid": tid,
        "name": None,        # OS/proc-reported thread name
        "py_name": tid_to_pyname.get(tid),  # Python threading name if available
        "cpu_percent": None,
        "state": None,
        "stack": None,
    }

    # Try to capture a Python stack trace for the thread if available
    try:
        frames = sys._current_frames()
        frame = frames.get(tid)
        if frame is not None:
            import traceback
            info["stack"] = ''.join(traceback.format_stack(frame))
    except Exception:
        pass

    # Try to collect /proc-based data (Linux only)
    try:
        if sys.platform.startswith("linux"):
            base = f"/proc/{proc.pid}/task/{tid}"

            def _read_text(path: str, max_bytes: int = 65536):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        return f.read(max_bytes)
                except Exception:
                    return None

            def _parse_kv(text: str):
                d = {}
                if not text:
                    return d
                for line in text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        d[k.strip()] = v.strip()
                return d

            comm = _read_text(os.path.join(base, "comm"))
            status_raw = _read_text(os.path.join(base, "status"))
            status = _parse_kv(status_raw) if status_raw else {}
            wchan = _read_text(os.path.join(base, "wchan"))
            sched = _read_text(os.path.join(base, "sched"))
            stat = _read_text(os.path.join(base, "stat"))
            proc_stack = _read_text(os.path.join(base, "stack"))

            info["procfs"] = {
                "comm": (comm.strip() if comm else None),
                "wchan": (wchan.strip() if wchan else None),
                "sched": sched,
                "stat": stat,
                "stack": proc_stack,
                "status": status if status else None,
                "status_raw": status_raw,
            }
            # default state from /proc if not provided elsewhere
            if info.get("state") is None and status.get("State"):
                info["state"] = status.get("State")
            if info.get("name") is None and status.get("Name"):
                info["name"] = status.get("Name")
            if info.get("name") is None and comm:
                info["name"] = comm.strip()
    except Exception:
        # best-effort; ignore failures
        pass

    return JSONResponse(info)



@psutil_analyzer_router.get("/processes", name="list_processes")
async def list_processes(request: Request, q: str = "", limit: int = 300, sort: str = "rss", order: str = "desc"):
    """Return a lightweight list of system processes.

    Supports optional filtering and sorting parameters.
    - q: filter by name/username/cmdline substring (case-insensitive)
    - limit: max number of rows to return (default 300)
    - sort: one of rss, mem, pid (default rss)
    - order: asc or desc (default desc)
    """
    try:
        attrs = [
            "pid",
            "ppid",
            "name",
            "username",
            "status",
            "create_time",
            "memory_percent",
            "num_threads",
            "nice",
            "cmdline",
            "memory_info",
        ]
        rows = []
        q_lower = (q or "").lower()
        for p in psutil.process_iter(attrs=attrs, ad_value=None):
            info = p.info
            mi = info.get("memory_info")
            rss = None
            if mi is not None:
                rss = getattr(mi, "rss", None)
                if rss is None and isinstance(mi, (list, tuple)) and len(mi) > 0:
                    rss = mi[0]
            cmd = info.get("cmdline")
            if isinstance(cmd, (list, tuple)):
                cmd_str = " ".join(str(x) for x in cmd)
            elif isinstance(cmd, str):
                cmd_str = cmd
            else:
                cmd_str = ""
            name = info.get("name") or ""
            user = info.get("username") or ""
            # Filter
            if q_lower:
                hay = f"{name} {user} {cmd_str}".lower()
                if q_lower not in hay:
                    continue
            rows.append({
                "pid": info.get("pid"),
                "ppid": info.get("ppid"),
                "name": name,
                "username": user,
                "status": info.get("status"),
                "create_time": info.get("create_time"),
                "memory_percent": info.get("memory_percent"),
                "rss": rss,
                "num_threads": info.get("num_threads"),
                "nice": info.get("nice"),
                "cmdline": cmd_str,
            })
        total = len(rows)
        # Sorting
        key = None
        if sort == "mem":
            key = lambda r: (r.get("memory_percent") or 0.0)
        elif sort == "pid":
            key = lambda r: (r.get("pid") or 0)
        else:  # rss
            key = lambda r: (r.get("rss") or 0)
        rows.sort(key=key, reverse=(order != "asc"))
        # Limit
        if limit and limit > 0:
            rows = rows[: min(limit, 5000)]
        return JSONResponse({"total": total, "processes": rows})
    except Exception as e:
        # Return a safe error payload
        return JSONResponse({"total": 0, "processes": [], "error": str(e)}, status_code=500)
