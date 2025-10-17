import threading
from typing import ClassVar, Any

import psutil
from fastpluggy.core.widgets import AbstractWidget
from pydantic import BaseModel, Field


class PsutilAnalyzerWidget(AbstractWidget):
    widget_type: str = "psutil_analyzer"

    template_name: str = "memory_analyzer/psutil_analyzer.html.j2"

    class ConfigModel(BaseModel):
        class Config:
            title = "PSUtil Analyzer Widget Configuration"
        
        title: str = Field(default="PSUtil Memory Analysis Dashboard", description="Widget title")

    def __init__(self, **config: Any):
        super().__init__()
        cfg = self.ConfigModel(**config)
        self.title = cfg.title

    def process(self, **kwargs):
        """Render the PSUtil Analyzer widget using the template."""

        # Get process information using psutil
        process = psutil.Process()
        self.process_dict = process.as_dict()

        # Build map from OS native thread id -> Python thread name
        self.tid_to_pyname = {t.native_id: t.name for t in threading.enumerate() if t.native_id is not None}

        # Expose mapping for UI templates and JS to use when showing threads

        # Generate URLs for template
        request = kwargs.get('request')
        self.inspect_heap_url = str(request.url_for("current_heap"))
        # Provide URL template for per-thread detail endpoint
        try:
            self.thread_detail_url = str(request.url_for("thread_detail", tid="12345")).replace("12345", "{tid}")
        except Exception:
            self.thread_detail_url = None
        # Provide processes listing endpoint URL
        try:
            self.processes_url = str(request.url_for("list_processes"))
        except Exception:
            self.processes_url = None

        
