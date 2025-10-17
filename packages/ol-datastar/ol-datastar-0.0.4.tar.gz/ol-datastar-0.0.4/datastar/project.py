"""
User-facing interface for DataStar Projects
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .datastar_api import DatastarAPI
from ._defaults import DEFAULT_DESCRIPTION

if TYPE_CHECKING:
    from .macro import Macro
    from .connections.sandbox_connection import SandboxConnection


class Project:
    """High-level representation of a DataStar project."""

    _api_client: Optional[DatastarAPI] = None

    def __init__(
        self,
        name: str,
        *,
        description: str = "",
        existing_project_id: Optional[str] = None,
    ):
        """
        Create and persist a new project.
        """
        assert name
        self.name: str = name
        self.description: str = description or DEFAULT_DESCRIPTION

        self._macro_counter: int = 1

        if existing_project_id is not None:
            # Constructing from existing project
            self.id: str = existing_project_id
        else:
            # Constructing a new project
            self.id: str = self.api().create_project(
                name=self.name,
                description=self.description,
            )

    def _next_macro_name(self) -> str:
        counter: int = self._macro_counter
        self._macro_counter += 1
        return f"Macro {counter}"

    @classmethod
    def api(cls) -> DatastarAPI:
        if cls._api_client is None:
            cls._api_client = DatastarAPI()
        return cls._api_client

    @classmethod
    def get_projects(cls) -> List[str]:
        """
        Retrieve all project names visible to the authenticated user.
        """
        return [entry["name"] for entry in cls.api()._get_projects_json()]

    @classmethod
    def create(cls, name: str, description: str = "") -> "Project":
        """Create a new project using the configured credentials."""
        return cls(name=name, description=description)

    @classmethod
    def connect_to(cls, name: str) -> "Project":
        """
        Connect to an existing project by its name.

        Raises:
            ValueError: If no project with ``name`` is visible to the user.
        """
        target = name.lower()
        project_detail = cls.api().build_project_lookup().get(target)
        if project_detail is None:
            raise ValueError(f"No project named '{name}' found.")
        return cls._from_json(project_detail)

    def rename(self, name: str) -> None:
        """
        Rename this project.
        """
        self.api().update_project(self.id, name=name)
        self.name = name

    def update(self, *, description: str) -> None:
        """
        Update the project description.
        """
        self.api().update_project(self.id, description=description)
        self.description = description

    def delete(self) -> None:
        """
        Delete this project. The instance remains but further operations
        requiring the server state may fail.
        """
        self.api().delete_project(self.id)

    # ------------------------------------------------------------------
    # Macro management

    def get_macros(self) -> List[str]:
        """
        Retrieve macros associated with this project.
        """
        response = self.api().get_macros(self.id)

        macro_list: List[str] = []
        for item in response.get("items", []):
            macro_list.append(item["name"])

        return macro_list

    def add_macro(self, name: str = "", description: str = "") -> "Macro":
        """
        Add a new macro to this project.
        """
        from .macro import Macro

        return Macro(self, name=name, description=description)

    def get_macro(self, name: str) -> Optional["Macro"]:
        """
        Get a macro by name.
        """
        from .macro import Macro

        response = self.api().get_macros(self.id)

        for item in response["items"]:
            if item["name"] == name:
                return Macro._read_from(self, item)

        return None

    def delete_macro(self, name: str) -> None:
        """
        Delete the specified macro from this project using its name.
        """
        from .macro import Macro

        macro: Optional[Macro] = self.get_macro(name)

        if macro is not None:
            macro.delete()

    def get_sandbox(self) -> "SandboxConnection":
        """
        Get a Sandbox connection for this project
        """
        from .connections.sandbox_connection import SandboxConnection

        return SandboxConnection(self)

    # ------------------------------------------------------------------
    # Internal

    @classmethod
    def _from_json(cls, payload: Dict[str, Any]) -> "Project":

        existing_project_id = payload["id"]
        name = payload["name"]
        description = payload["description"]

        return Project(
            name=name, description=description, existing_project_id=existing_project_id
        )
