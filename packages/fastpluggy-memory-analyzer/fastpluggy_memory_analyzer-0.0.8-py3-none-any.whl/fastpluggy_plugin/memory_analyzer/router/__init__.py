from fastapi import APIRouter
from .psutil_analyzer import psutil_analyzer_router
from .endpoints_memory import endpoints_memory_router

# Main router for memory analyzer module
memory_analyzer_router = APIRouter(
    tags=["memory", "analyzer"],
)

# Include the psutil analyzer router
memory_analyzer_router.include_router(psutil_analyzer_router)

# Include the endpoints memory router
memory_analyzer_router.include_router(endpoints_memory_router)