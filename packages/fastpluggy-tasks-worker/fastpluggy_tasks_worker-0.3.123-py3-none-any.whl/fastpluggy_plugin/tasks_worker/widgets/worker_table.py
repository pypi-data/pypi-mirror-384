
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastpluggy.core.widgets import AbstractWidget

from ..broker.factory import get_broker


class WorkerTableView(AbstractWidget):
    """
    Full custom widget with its own Jinja template, similar to TaskFormView.
    It renders a Tabler-styled table of workers with an Info modal per row (modal markup in template).
    """

    widget_type = "worker_table_view"
    template_name: str = "tasks_worker/widgets/worker_table.html.j2"

    # Default columns mapping for workers table
    DEFAULT_FIELDS = [
        "worker_id",
        "host",
        "pid",
        "role",
        "capacity",
        "running",
        "stale",
        "topics",
        "last_seen_min",
        "details",
    ]

    DEFAULT_HEADERS: Dict[str, str] = {
        "worker_id": "Worker ID",
        "host": "Host",
        "pid": "PID",
        "role": "Role",
        "capacity": "Capacity",
        "running": "Running",
        "stale": "Stale",
        "topics": "Topics",
        "last_seen_min": "Last seen",
        "details": "Info",
    }

    def __init__(
        self,
        *,
        title: str = "Workers",
        data: Optional[List[Dict[str, Any]]] = None,
        fields: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        broker: Optional[Any] = None,
        include_tasks: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self._input_data = data
        self.fields = fields or self.DEFAULT_FIELDS
        self.headers = dict(self.DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        self.broker = broker
        self.include_tasks = include_tasks
        # processed attributes for template
        self.data: List[Dict[str, Any]] = []

    def _enrich_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        now_utc = datetime.now(timezone.utc)
        out: List[Dict[str, Any]] = []
        for w in rows:
            w = dict(w)
            # compute last_seen_min safe HTML string (template will mark safe)
            try:
                ls = w.get("last_seen")
                if isinstance(ls, str) and ls:
                    try:
                        dt = datetime.fromisoformat(ls)
                    except ValueError:
                        dt = None
                    if dt is not None:
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        minutes = int(max(0, (now_utc - dt).total_seconds()) // 60)
                        w["last_seen_min"] = f'<span title="{ls}">{minutes} min</span>'
                    else:
                        w["last_seen_min"] = "-"
                else:
                    w["last_seen_min"] = "-"
            except Exception:
                w["last_seen_min"] = "-"

            # Provide a stable dialog id for the template; modal markup lives in template.
            try:
                base_id = str(w.get("worker_id") or f"{w.get('host','')}-{w.get('pid','')}")
                safe_id = "".join(ch if (ch.isalnum() or ch in ("-", "_")) else "-" for ch in base_id)
                w["dialog_id"] = f"wkdlg-{safe_id}"
            except Exception:
                pass

            out.append(w)
        return out

    def process(self, **kwargs):
        # load data if not provided
        data: Optional[List[Dict[str, Any]]] = self._input_data
        if data is None:
            try:
                b = self.broker or get_broker()
                items = b.get_workers(include_tasks=self.include_tasks) or []
                data = [asdict(i) if is_dataclass(i) else i for i in items]
            except Exception:
                data = []
        data = list(data or [])
        self.data = self._enrich_rows(data)
        # expose headers/fields to template
        self.use_fields = self.fields
        self.use_headers = self.headers
        self.table_id = kwargs.get("table_id") or "workers-table"
        self.card_class = kwargs.get("card_class") or "card"
        self.table_class = kwargs.get("table_class") or "table table-vcenter"
