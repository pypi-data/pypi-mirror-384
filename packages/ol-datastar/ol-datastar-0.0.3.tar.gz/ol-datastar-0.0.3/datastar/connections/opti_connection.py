"""Connection subclass for Optilogic databases."""

from __future__ import annotations
from typing import Any, Dict, Optional
from ..connection import Connection


class OptiConnection(Connection):
    """Represents an Optilogic database connection."""

    def __init__(
        self,
        *,
        name: str = "",
        description: str = "",
        schema: str = "public",
        storage_id: Optional[str] = None,
        storage_name: Optional[str] = None,
    ):
        if bool(storage_id) == bool(storage_name):
            raise ValueError("Provide exactly one of storage_id or storage_name.")

        self.schema: str = schema
        self.storage_id: Optional[str] = storage_id
        self.storage_name: Optional[str] = storage_name

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(name=name, description=description)

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_connection_type(self) -> str:
        return "optidb"

    def _to_configuration(self) -> Dict[str, Any]:

        configuration: Dict[str, Optional[str]] = {
            "schema": self.schema,
            "storageId": self.storage_id,
            "storageName": self.storage_name,
        }

        return configuration

    def _from_configuration(self, payload: Dict[str, Any]) -> None:

        self.storage_id = payload.get("storageId")
        self.storage_name = payload.get("storageName")
        self.schema = payload.get("schema", "public")
