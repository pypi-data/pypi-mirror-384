"""Task type for executing Python code."""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from ..task import Task

if TYPE_CHECKING:
    from ..macro import Macro


class RunPythonTask(Task):
    """Runs Python scripts within the macro."""

    def __init__(
        self,
        macro: "Macro",
        *,
        name: str = "",
        description: str = "",
        filename: str = "",
        directory_path: str = "",
    ):
        self.filename = filename
        self.directory_path = directory_path

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(macro=macro, name=name, description=description)

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_task_type(self) -> str:
        return "runpython"

    def _to_configuration(self) -> Dict[str, Any]:

        configuration: Dict[str, Any] = {}

        configuration["file"] = {
            "filename": self.filename,
            "directoryPath": self.directory_path,
        }
        return configuration

    def _from_configuration(self, configuration: Dict[str, Any]) -> None:

        file = configuration["file"]
        self.filename = file["filename"]
        self.directory_path = file["directoryPath"]
