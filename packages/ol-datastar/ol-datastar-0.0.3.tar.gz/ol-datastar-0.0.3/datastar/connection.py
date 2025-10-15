"""
High-level Connection helper.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Optional

from .datastar_api import DatastarAPI
from ._defaults import DEFAULT_DESCRIPTION


class Connection(ABC):
    """Represents a connection scoped to a project."""

    _auto_name_counter: int = 1
    _api_client: ClassVar[Optional[DatastarAPI]] = None

    @classmethod
    def auto_name_counter(cls) -> int:
        counter = Connection._auto_name_counter
        Connection._auto_name_counter += 1
        return counter

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sandbox: Optional[bool] = False,
    ):
        super().__init__()
        self.name = name or f"Connection {self.auto_name_counter()}"
        self.description = description or DEFAULT_DESCRIPTION

        # Note: Sandbox is a special case, it is not persisted
        if sandbox:
            self.id = DatastarAPI.SANDBOX_CONNECTOR_ID
        else:
            self.id: str = self._persist_new()

    @classmethod
    def api(cls) -> DatastarAPI:
        if cls._api_client is None:
            cls._api_client = DatastarAPI()
        return cls._api_client

    # ------------------------------------------------------------------
    # Internal

    @classmethod
    def _name_to_id(cls, name: str) -> str | None:
        """
        Resolve a connector identifier from its display name.

        Args:
            name: Connector name to search for.

        Returns:
            The connector UUID as a string.

        Raises:
            ValueError: If the name is empty or no connector matches.
        """

        if not name or not name.strip():
            raise ValueError("Connector name is required.")

        target = name.strip().lower()
        response = cls.api().get_connectors()
        for entry in DatastarAPI.coerce_collection(response):
            candidate = entry.get("name")
            if isinstance(candidate, str) and candidate.strip().lower() == target:
                connector_id = entry.get("id")
                if connector_id:
                    return str(connector_id)

        return None

    # Lifecycle helpers
    # ------------------------------------------------------------------

    def _persist_new(self) -> str:
        payload = self._to_json()
        config_fields = {
            key: value
            for key, value in payload.items()
            if key not in {"name", "type", "description"}
        }
        response = self.api().create_connection(
            name=str(self.name),
            connection_type=payload["type"],
            configuration=config_fields,
            description=payload.get("description"),
        )
        return str(DatastarAPI.extract_first(response)["id"])

    def rename(self, name: str) -> None:
        assert self.id
        assert name and name.strip()
        self.api().update_connection(self.id, name=name.strip())
        self.name = str(name)

    def update(self, *, description: str) -> None:
        assert self.id
        self.api().update_connection(self.id, description=description)

    def delete(self) -> None:
        assert self.id
        self.api().delete_connection(self.id)

    # ------------------------------------------------------------------
    # Connector metadata helpers

    # TODO: Test this
    def get_tables(self, *, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve available tables for this connection.
        """
        return self.api().get_connector_tables(self.id, project_id=project_id)

    # TODO: look at this
    def get_schema(self, table: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve schema details for the specified table.
        """
        return self.api().get_connector_schema(self.id, table=table)

    # TODO: Preview connection?

    # ------------------------------------------------------------------
    # JSON translation helpers

    def _to_json(self) -> Dict[str, Any]:

        configuration: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "type": self.get_connection_type(),
        }

        # Add subclass data via overriden method
        configuration.update(self._to_configuration())

        return configuration

    def _from_json(self, payload: Dict[str, Any]) -> None:

        self.id = payload["id"]
        self.name = payload["name"]
        self.description = payload.get("description")

        # Add subclass data via overridden method
        self._from_configuration(payload.get("configuration"))

    # ------------------------------------------------------------------
    # Abstract methods

    @abstractmethod
    def get_connection_type(self) -> str:
        assert False

    @abstractmethod
    def _from_configuration(self, payload: Dict[str, Any]) -> None:
        assert False

    @abstractmethod
    def _to_configuration(self) -> Dict[str, Any]:
        assert False
