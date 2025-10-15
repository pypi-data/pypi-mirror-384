"""Task type for exporting data."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional, TYPE_CHECKING

from ..connection import Connection

from ..task import Task
from ..converters import mapping_json_to_tuples, mapping_tuples_to_json

if TYPE_CHECKING:
    from ..macro import Macro


class ExportTask(Task):
    """Exports project data to an external destination."""

    def __init__(
        self,
        macro: "Macro",
        *,
        name: str = "",
        description: str = "",
        source_connection: Connection,
        destination_connection: Optional[Connection] = None,
        source_table: str = "",
        destination_table: str = "",
        destination_table_type: str = "new",
        destination_table_action: str = "replace",
        condition: str = "",
        mappings: List[Tuple[str, str]] = [],
        file_name: str = "",
    ):
        self.source_connection_id = source_connection.id
        if destination_connection is not None:
            self.destination_connection_id = destination_connection.id
        else:
            self.destination_connection_id = ""

        self.source_table = source_table
        self.destination_table = destination_table
        self.destination_table_type = destination_table_type or "new"
        self.destination_table_action = destination_table_action or "replace"
        self.condition = condition
        self.mappings = mappings or []
        self.file_name = file_name

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(macro=macro, name=name, description=description)

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_task_type(self) -> str:
        return "export"

    def _to_configuration(self) -> Dict[str, Any]:

        configuration: Dict[str, Any] = {}

        # Add source connection
        configuration["source"] = {
            "connectorId": self.source_connection_id,
            "table": str(self.source_table),
        }

        # Add destination (file or connection)
        if self.file_name:
            configuration["destination"] = {"type": "file", "fileName": self.file_name}
        else:
            configuration["destination"] = {
                "type": "connector",
                "connectorId": self.destination_connection_id,
                "tableAction": self.destination_table_action,
                "tableType": self.destination_table_type,
            }
            if self.destination_table_type == "new":
                configuration["destination"]["newTableName"] = self.destination_table
            else:
                configuration["destination"]["table"] = self.destination_table

        if self.condition:
            configuration["condition"] = self.condition

        configuration["mappings"] = mapping_tuples_to_json(self.mappings)

        return configuration

    def _from_configuration(self, configuration: Dict[str, Any]) -> None:

        source_section = configuration["source"]
        destination_section = configuration["destination"]

        self.source_connection_id = source_section.get("connectorId")
        self.source_table = source_section.get("table")

        self.destination_connection_id = destination_section.get("connectorId")
        self.destination_table = destination_section.get(
            "newTableName"
        ) or destination_section.get("table")
        self.destination_table_type = destination_section.get("tableType")
        self.destination_table_action = destination_section.get("tableAction")

        self.condition = configuration.get("condition")

        self.mappings = configuration.get("mappings") or {}
