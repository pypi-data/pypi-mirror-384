"""Connection subclass for Cosmic Frog models."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..connection import Connection


class FrogModelConnection(Connection):
    """Represents a Cosmic Frog model connection."""

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        storage_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        if (not storage_id) and (not model_name):
            raise ValueError("Either storage_id or model_name must be provided.")

        self.storage_id = storage_id
        self.model_name = model_name

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(name=name, description=description)

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_connection_type(self) -> str:
        return "cosmicfrog"

    def _to_configuration(self) -> Dict[str, Any]:

        configuration: Dict[str, Optional[str]] = {
            "storageId": self.storage_id,
            "modelName": self.model_name,
        }

        return configuration

    def _from_configuration(self, payload: Dict[str, Any]) -> None:

        self.storage_id = payload.get("storageId")
        self.model_name = payload.get("modelName")
