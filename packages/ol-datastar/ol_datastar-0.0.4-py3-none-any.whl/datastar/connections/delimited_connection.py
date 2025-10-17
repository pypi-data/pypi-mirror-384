"""Connection subclass for delimited files."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..connection import Connection


class DelimitedConnection(Connection):
    """Represents a delimited file connection."""

    def __init__(
        self,
        *,
        name: str = "",
        description: str = "",
        path: str = "",
        delimiter: str = ",",
        encoding: str = "",
    ):
        if not path:
            raise ValueError("path is required for DelimitedConnection.")

        self.path = path
        self.delimiter = delimiter
        self.encoding = encoding

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(
            name=name,
            description=description,
        )

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_connection_type(self) -> str:
        return "dsv"

    def _to_configuration(self) -> Dict[str, Any]:

        configuration: Dict[str, Any] = {
            "path": self.path,
            "delimiter": self.delimiter,
            "encoding": self.encoding,
        }

        return configuration

    def _from_configuration(self, payload: Dict[str, Any]) -> None:

        self.path = payload.get("path")
        self.delimiter = payload.get("delimiter")
        self.encoding = payload.get("encoding")
