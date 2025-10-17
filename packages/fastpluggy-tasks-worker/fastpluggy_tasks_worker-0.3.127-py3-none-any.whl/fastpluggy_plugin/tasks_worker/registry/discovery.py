import importlib
import inspect
import pkgutil

from loguru import logger

from fastpluggy.fastpluggy import FastPluggy
from .utils import _unwrap, merge_task_metadata


def discover_tasks_from_loaded_modules(fast_pluggy: FastPluggy) -> int:
    """
    Discover functions decorated with @TaskWorker.register in all loaded FastPluggy modules.
    Returns the count of discovered tasks.
    """
    logger.info("🔍 Starting task discovery from loaded FastPluggy modules (including submodules)...")
    discovered = 0

    loaded_modules = fast_pluggy.get_manager().modules

    for module_name, module_meta in loaded_modules.items():
        base_package = getattr(module_meta, "package_name", None)
        if not base_package:
            continue

        tasks_module_name = f"{base_package}.tasks"

        try:
            base_tasks_module = importlib.import_module(tasks_module_name)
        except ModuleNotFoundError:
            logger.debug(f"❌ No tasks module in {module_name} ({tasks_module_name})")
            continue
        except Exception as e:
            logger.warning(f"⚠️ Failed to import {tasks_module_name}: {e}")
            continue

        modules_to_check = [base_tasks_module]

        if hasattr(base_tasks_module, "__path__"):  # It's a package
            for submodule_info in pkgutil.walk_packages(base_tasks_module.__path__, prefix=tasks_module_name + "."):
                try:
                    submodule = importlib.import_module(submodule_info.name)
                    modules_to_check.append(submodule)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to import submodule {submodule_info.name}: {e}")

        for mod in modules_to_check:
            for _, obj in inspect.getmembers(mod, inspect.isfunction):
                real_fn = _unwrap(obj)
                if hasattr(real_fn, "_task_metadata"):
                    task_name = real_fn._task_metadata["name"]
                    logger.info(f"✅ Discovered task: {task_name} from module {mod.__name__}")
                    discovered += 1
                    merge_task_metadata(obj, discovery_method="discover_tasks_from_loaded_modules")

    logger.info(f"✅ Task discovery complete: {discovered} task(s) found.")
    return discovered



