"""
Helper mapping type as string to Task subclasses
"""

from typing import Dict, Any
from .tasks.task_import import ImportTask
from .tasks.task_export import ExportTask
from .tasks.task_run_sql import RunSQLTask
from .tasks.task_run_python import RunPythonTask
from .tasks.task_start import StartTask

# Note: This supports macro.get_task to return correct subclass based on API response
TASK_TYPE_MAP: Dict[str, Any] = {
    "import": ImportTask,
    "export": ExportTask,
    "runsql": RunSQLTask,
    "runpython": RunPythonTask,
    "start": StartTask,
}


def get_task_class(task_type: str):
    return TASK_TYPE_MAP[task_type]
