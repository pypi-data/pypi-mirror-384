"""Connection subclass for Excel files."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..connection import Connection


class ExcelConnection(Connection):
    """Represents an Excel connection."""

    default_connection_type = "excel"

    def __init__(
        self,
        *,
        path: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sheet_name: Optional[str] = None,
        workbook_password: Optional[str] = None,
    ):
        if not path:
            raise ValueError("path is required for ExcelConnection.")

        self.path = str(path)
        self.sheet_name = None if sheet_name is None else str(sheet_name)
        self.workbook_password = (
            None if workbook_password is None else str(workbook_password)
        )

        # Note: base will persist, which calls back into subclass, so call init here at end
        super().__init__(name=name, description=description)

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_connection_type(self) -> str:
        return "dsv"

    def _to_configuration(self) -> Dict[str, Any]:
        config: Dict[str, Any] = {"path": self.path}
        if self.sheet_name:
            config["sheetName"] = self.sheet_name
        if self.workbook_password:
            config["password"] = self.workbook_password
        return config

    def _from_configuration(self, payload: Dict[str, Any]) -> None:
        if "path" in payload:
            path_value = payload.get("path")
            self.path = None if path_value is None else str(path_value)
        elif not hasattr(self, "path"):
            self.path = None
        if "sheetName" in payload:
            sheet_value = payload.get("sheetName")
            self.sheet_name = None if sheet_value is None else str(sheet_value)
        elif not hasattr(self, "sheet_name"):
            self.sheet_name = None
        if "password" in payload:
            password_value = payload.get("password")
            self.workbook_password = (
                None if password_value is None else str(password_value)
            )
        elif not hasattr(self, "workbook_password"):
            self.workbook_password = None
