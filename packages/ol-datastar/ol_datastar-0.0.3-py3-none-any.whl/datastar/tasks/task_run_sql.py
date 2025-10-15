"""Task type for SQL execution."""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from ..connection import Connection
from ..task import Task

if TYPE_CHECKING:
    from ..macro import Macro


class RunSQLTask(Task):
    """Executes SQL statements as part of a macro."""

    def __init__(
        self,
        macro: "Macro",
        *,
        name: str = "",
        description: str = "",
        query: str = "",
        connection: Connection,
    ):
        self.query = query
        self.connection_id = connection.id

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(macro=macro, name=name, description=description)

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_task_type(self) -> str:
        return "runsql"

    def _to_configuration(self) -> Dict[str, Any]:

        target: Dict[str, str] = {"connectorId": self.connection_id}

        return {"query": self.query, "target": target}

    def _from_configuration(self, configuration: Dict[str, Any]) -> None:

        self.query = configuration["query"]

        self.connection_id = configuration["target"]["connectorId"]
