import inspect
import logging
import os
from typing import Callable, Dict, Any

from fastpluggy.fastpluggy import FastPluggy
from fastpluggy.core.models_tools.shared import ModelToolsShared

TASK_REGISTRY_KEY = "task_registry"


class TaskRegistry:
    def __init__(self):
        self._seen_names = set()  # track duplicates

    @staticmethod
    def _reserved_keys() -> set[str]:
        """
        Dynamically compute reserved keys from the register() signature
        plus internal metadata fields we always populate.
        """
        sig = inspect.signature(TaskRegistry.register)
        reserved = {
            p.name
            for p in sig.parameters.values()
            if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
               and p.name not in {"self", "cls", "extra"}
        }
        # Add computed metadata fields
        reserved.update({"module", "package", "source_file", "qualified_name"})
        return reserved

    def register(
            self,
            name: str = None,
            description: str = "",
            tags: list[str] = None,
            schedule: str = None,
            max_retries: int = 0,
            allow_concurrent: bool = True,
            task_type: str = "native",
            topic: str | None = None,
            **extra: Any,
    ):

        def decorator(func: Callable):
            task_name = name or func.__name__

            # ── CONFLICT DETECTION ──────────────────────────────────────────
            if task_name in self._seen_names:
                logging.warning(f"Duplicate task name detected: {task_name}")
            self._seen_names.add(task_name)
            # ─────────────────────────────────────────────────────────────────

            module = func.__module__
            source_file = inspect.getfile(func)
            package = module.split(".")[0] if "." in module else module

            # Split extras into safe bucket to avoid overriding reserved keys
            reserved = self._reserved_keys()
            extras_clean: Dict[str, Any] = {}
            for k, v in (extra or {}).items():
                if k in reserved:
                    logging.warning(
                        f"[task:{task_name}] extra field '{k}' conflicts with a reserved key; "
                        f"ignoring in extras (use the proper parameter instead)."
                    )
                    continue
                extras_clean[k] = v

            # safe to attach: func is a pure function or decorator wrapper
            func._task_metadata = {
                "name": task_name,
                "description": description,
                "tags": tags or [],
                "schedule": schedule,
                "max_retries": max_retries,
                "allow_concurrent": allow_concurrent,
                "task_type": task_type,
                "topic": topic,
                "module": module,
                "package": package,
                "source_file": os.path.abspath(source_file),
                "qualified_name": func.__qualname__,
                "extras": extras_clean,
            }
            # save task by function name into registry
            self._save_to_global(func.__qualname__, func)
            return func

        return decorator

    def _save_to_global(self, name: str, func: Callable):
        current = FastPluggy.get_global(TASK_REGISTRY_KEY, default={})
        current[name] = func
        FastPluggy.register_global(TASK_REGISTRY_KEY, current)

    def get(self, name: str) -> Callable | None:
        """
        Retrieve a task by identifier.
        Supports:
        - simple registry key (qualified_name)
        - "module:qualname"
        - "module.qualname"
        """
        registry = FastPluggy.get_global(TASK_REGISTRY_KEY, {})
        # Direct hit
        if name in registry:
            return registry.get(name)
        # module:qualname
        if ":" in name:
            module, qual = name.split(":", 1)
            # Try via metadata match
            return self.get_by_fullname(f"{module}.{qual}")
        # module.qualname
        if "." in name:
            # Try full metadata match first
            func = self.get_by_fullname(name)
            if func:
                return func
            # Fallback to last segment (bare qualified_name)
            short = name.rsplit(".", 1)[-1]
            return registry.get(short)
        # Simple name fallback
        return registry.get(name)

    def get_by_fullname(self, fullname: str) -> Callable | None:
        """
        Retrieve a task by its full identifier, including module and qualified name,
        e.g. 'my_module.MyClass.my_method'.
        """
        # Fetch the registry of tasks
        registry: Dict[str, Callable] = FastPluggy.get_global(TASK_REGISTRY_KEY, {})
        # Iterate through registered functions and match on metadata
        for func in registry.values():
            meta = getattr(func, "_task_metadata", None)
            if not meta:
                continue
            module = meta.get("module")
            qname = meta.get("qualified_name")
            # Construct full name and compare
            if module and qname and f"{module}.{qname}" == fullname:
                return func
        return None

    def all(self) -> Dict[str, Callable]:
        return FastPluggy.get_global(TASK_REGISTRY_KEY, {})

    def list_metadata(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "qualified_name": meta.get("qualified_name"),
                "module": meta.get("module"),
                "package": meta.get("package"),
                "source_file": meta.get("source_file"),
                "schedule": meta.get("schedule"),
                "max_retries": meta.get("max_retries", 0),
                "description": meta.get("description") or "",
                "docstring": inspect.getdoc(func),
                "tags": meta.get("tags", []),
                "task_type": meta.get("task_type", "native"),
                "topic": meta.get("topic"),
                "is_async": inspect.iscoroutinefunction(func),
                "allow_concurrent": meta.get("allow_concurrent"),
                "params": ModelToolsShared.get_model_metadata(func),
                "extras": meta.get("extras", {}),
            }
            for name, func in self.all().items()
            if (meta := getattr(func, "_task_metadata", None))
        ]

    def registry_summary(self) -> dict:
        # todo : will be usefull for stats on frontend page of registry
        tasks = self.list_metadata()
        return {
            "total": len(tasks),
            "async": sum(1 for t in tasks if t["is_async"]),
            "sync": sum(1 for t in tasks if not t["is_async"]),
            "tags": sorted({tag for t in tasks for tag in t["tags"]}),
        }


# Instantiate it globally
task_registry = TaskRegistry()
