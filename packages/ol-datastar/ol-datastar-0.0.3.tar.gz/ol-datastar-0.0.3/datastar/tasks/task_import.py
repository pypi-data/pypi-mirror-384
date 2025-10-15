"""Task type for data import operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from ..connection import Connection
from ..task import Task
from ..converters import mapping_json_to_tuples, mapping_tuples_to_json

if TYPE_CHECKING:
    from ..macro import Macro


class ImportTask(Task):
    """Loads data into the project environment."""

    def __init__(
        self,
        macro: "Macro",
        *,
        task_id: str = "",
        name: str = "",
        description: str = "",
        source_connection: Connection,
        destination_connection: Connection,
        source_table: str = "",
        destination_table: str = "",
        destination_table_type: str = "new",
        destination_table_action: str = "replace",
        condition: str = "",
        mappings: Optional[List[Tuple[str, str]]] = [],
    ) -> None:
        from ..connections.delimited_connection import DelimitedConnection

        # No source table needed for a dsv connection
        assert source_table or isinstance(source_connection, DelimitedConnection)

        self.source_connection_id = source_connection.id
        self.destination_connection_id = destination_connection.id

        # TODO: Don't allow set table for csv
        self.source_table = str(source_table)
        self.destination_table = destination_table
        self.destination_table_type = destination_table_type
        self.destination_table_action = str(
            destination_table_action or "replace"
        ).lower()
        self.condition = condition
        self.mappings = mappings or []

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(
            task_id=task_id, macro=macro, name=name, description=description
        )

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_task_type(self) -> str:
        return "import"

    def _to_configuration(self) -> Dict[str, Any]:

        configuration: Dict[str, Any] = {
            "source": {
                "connectorId": self.source_connection_id,
                "table": str(self.source_table),
            },
            "destination": {
                "connectorId": self.destination_connection_id,
                "tableAction": self.destination_table_action,
                "tableType": self.destination_table_type,
            },
        }

        destination_table = str(self.destination_table)
        if self.destination_table_type == "new":
            configuration["destination"]["newTableName"] = destination_table
        else:
            configuration["destination"]["table"] = destination_table

        if self.condition:
            configuration["condition"] = self.condition

        configuration["mappings"] = mapping_tuples_to_json(self.mappings)

        return configuration

    def _from_configuration(self, configuration: Dict[str, Any]) -> None:

        source_section = configuration.get("source", {})
        destination_section = configuration.get("destination", {})

        self.source_connection_id = source_section.get("connectorId")
        self.destination_connection_id = destination_section.get("connectorId")

        self.source_table = source_section.get("table")

        self.destination_table = destination_section.get(
            "newTableName"
        ) or destination_section.get("table")

        self.destination_table_type = destination_section.get("tableType")
        self.destination_table_action = destination_section.get("tableAction")

        self.condition = configuration.get("condition")

        self.mappings = configuration.get("mappings")
