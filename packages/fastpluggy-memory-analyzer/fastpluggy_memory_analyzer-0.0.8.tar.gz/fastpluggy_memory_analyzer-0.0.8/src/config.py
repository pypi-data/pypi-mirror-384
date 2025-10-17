from pydantic import Field
from pydantic_settings import BaseSettings


class MemoryMonitorSettings(BaseSettings):
    """Settings for the memory monitor plugin."""
    sampling_rate: float = Field(0.15, description="Fraction of requests to sample for Pympler snapshots.")

    monitor_all_endpoints: bool = Field(False, description="When True, monitor all endpoints without requiring debug header or sampling.") # todo rename to monitor_endpoints to enabler the middleware
    debug_header: str = Field("X-Debug-Mem", description="Header to force a snapshot on a request when set to 1/true.")

    class Config:
        env_prefix = "FP_MEMORY_"
