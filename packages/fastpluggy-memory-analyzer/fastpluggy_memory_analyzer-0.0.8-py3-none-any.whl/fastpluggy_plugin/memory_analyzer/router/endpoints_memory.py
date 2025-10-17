import psutil
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastpluggy.core.auth import require_authentication
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.widgets import CustomTemplateWidget

from ..store import store
from ..config import MemoryMonitorSettings

# Create router with authentication
endpoints_memory_router = APIRouter(
    prefix="/endpoints-memory",
    tags=["debug", "memory", "endpoints"],
    dependencies=[Depends(require_authentication)],
)


@menu_entry(label="Endpoints Memory Monitor")
@endpoints_memory_router.get("/", name="endpoints_memory_dashboard")
async def endpoints_memory_dashboard(request: Request, view_builder=Depends(get_view_builder)):
    """Dashboard for monitoring memory usage per endpoint."""
    # Import here to avoid circular imports
    try:
        from home.src.domains.memory_monitor.store import store
    except ImportError:
        # Fallback if store is not available
        data = []
        rss = uss = pss = 0
    else:
        data = store.snapshot()
        proc = psutil.Process()
        mi = proc.memory_full_info()
        rss = mi.rss
        uss = getattr(mi, "uss", None)
        pss = getattr(mi, "pss", None)
    
    settings = MemoryMonitorSettings()

    context = {
        "rows": data,
        "rss": rss,
        "uss": uss,
        "pss": pss,
        "data_url": str(request.url_for("endpoints_memory_data")),
        "monitor_all_status_url": str(request.url_for("get_endpoints_monitor_all_status")),
        "monitor_all_toggle_url": str(request.url_for("toggle_endpoints_monitor_all")),
        "detail_url_base": str(request.url_for("endpoints_memory_detail")),
        "debug_header": settings.debug_header,
    }
    
    return view_builder.generate(
        request,
        title="Endpoints Memory Dashboard",
        widgets=[
            CustomTemplateWidget(
                template_name="memory_analyzer/endpoints_dashboard.html.j2",
                context=context
            )
        ]
    )


@endpoints_memory_router.get("/data")
async def endpoints_memory_data():
    """Get endpoints memory data as JSON."""
    try:
        from home.src.domains.memory_monitor.store import store
        return JSONResponse(store.snapshot())
    except ImportError:
        return JSONResponse([])


@endpoints_memory_router.get("/detail", name="endpoints_memory_detail")
async def endpoints_memory_detail(request: Request, method: str, endpoint: str, view_builder=Depends(get_view_builder)):
    """Detail view for specific endpoint memory usage."""
    try:
        from home.src.domains.memory_monitor.store import store
        st = store.get(method, endpoint)
        if not st:
            raise HTTPException(404, "Unknown endpoint")
    except ImportError:
        raise HTTPException(503, "Memory monitor store not available")
    
    context = {
        "method": method,
        "endpoint": endpoint,
        "stats": st,
    }
    
    return view_builder.generate(
        request,
        title="Endpoint Memory Detail",
        widgets=[
            CustomTemplateWidget(
                template_name="memory_analyzer/endpoints_detail.html.j2",
                context=context
            )
        ]
    )


@endpoints_memory_router.get("/config/monitor-all")
async def get_endpoints_monitor_all_status():
    """Get current status of monitor_all_endpoints setting."""
    try:
        return JSONResponse({"monitor_all_endpoints": store.get_monitor_all_endpoints()})
    except ImportError:
        return JSONResponse({"monitor_all_endpoints": False})


@endpoints_memory_router.post("/config/monitor-all/toggle")
async def toggle_endpoints_monitor_all():
    """Toggle the monitor_all_endpoints setting."""
    try:
        new_state = store.toggle_monitor_all_endpoints()
        return JSONResponse({"monitor_all_endpoints": new_state, "message": f"Monitor all endpoints {'enabled' if new_state else 'disabled'}"})
    except ImportError:
        return JSONResponse({"error": "Memory monitor store not available"}, status_code=503)