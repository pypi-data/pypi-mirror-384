"""
Core API infrastructure for the DataStar SDK.

Provides the base client that handles authentication, session setup,
and making HTTP requests. Resource-specific APIs (projects, connectors,
etc.) inherit from this base class to expose higher-level operations.
"""

import os
from typing import Any, Dict, List, Optional
import traceback
from json import JSONDecodeError
import requests
from requests import request, Response

DOMAIN: str = "https://api.optilogic.app"
VERSION: int = 0
API_BASE = f"{DOMAIN}/v{VERSION}/"


class ApiError(Exception):
    """Exception class to contain dependency on requests module to this file."""

    def __init__(
        self, message: str, original_exception: Optional[BaseException] = None
    ):
        super().__init__(message)
        self.original_exception: Optional[BaseException] = original_exception
        self.trace: str = traceback.format_exc()


class DatastarAPI:
    """
    Base class for DataStar API clients.

    Handles authentication, base URL management, and HTTP request
    execution. Subclasses provide resource-specific helpers.

    ``app_key`` may be set by user code *once* prior to instantiation of any
    API objects. When left unset the constructor will fall back to the
    ``OPTILOGIC_APPKEY`` environment variable.
    """

    app_key: Optional[str] = None
    DATASTAR_API_DEFAULT_TIMEOUT: int = 60
    SANDBOX_CONNECTOR_ID: str = "00000000-0000-0000-0000-000000000000"

    def __init__(self):
        """
        Initialize the DataStar API base client.

        :param domain: API domain, defaults to https://api.optilogic.app
        :param version: API version, defaults to 0
        """

        if DatastarAPI.app_key is None:
            DatastarAPI.app_key = os.getenv("OPTILOGIC_APPKEY")

        if not DatastarAPI.app_key:
            raise ValueError(
                "API key is required. Set DatastarAPI.app_key or provide the OPTILOGIC_APPKEY environment variable. "
                "Get your key at: https://optilogic.app/#/user-account?tab=appkey"
            )

        if len(DatastarAPI.app_key) != 51 or not DatastarAPI.app_key.startswith("op_"):
            raise ValueError(
                "Valid appkey is required (format: op_..., 51 characters). "
                "Get your key at: https://optilogic.app/#/user-account?tab=appkey"
            )

        # Setup request headers
        self.auth_req_header = {
            "x-app-key": DatastarAPI.app_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        :param method: HTTP method (GET, POST, PUT, DELETE, etc.)
        :param endpoint: API endpoint path (without base URL)
        :param data: Request body data
        :param params: URL query parameters
        :return: Response data as dictionary
        """

        url = f"{API_BASE}{endpoint}"

        try:
            # print("REQUEST BODY:", data)

            response: Response = request(
                method=method,
                url=url,
                headers=self.auth_req_header,
                json=data,
                params=params,
                timeout=self.DATASTAR_API_DEFAULT_TIMEOUT,
            )

            response.raise_for_status()

            # Try to parse JSON response
            try:
                return response.json()
            except JSONDecodeError:
                # If response is not JSON, return raw text
                return {"result": "success", "data": response.text}

        # Exceptions from requests library are wrapped to confine the module dependecy to this file
        except requests.exceptions.RequestException as e:
            print("=== REQUEST EXCEPTION ===")
            print(f"Type: {type(e)}")
            print(f"Args: {e.args}")
            print(f"Message: {e}")
            print(f"Response object: {getattr(e, 'response', None)}")
            print(f"Request object: {getattr(e, 'request', None)}")
            print("Full traceback:")
            traceback.print_exc()
            raise ApiError(f"HTTP request failed: {e}", e) from e

    # ==================== PROJECT RELATED ====================

    def _get_projects_json(self) -> List[Dict[str, Any]]:
        """
        Retrieve project payloads visible to the authenticated user.
        """
        response = self._request("GET", "datastar/projects")

        payloads: List[Dict[str, Any]] = []
        for entry in self.coerce_collection(response):
            name = entry.get("name")
            if name is None:
                raise ValueError("Project payload missing 'name'.")
            payloads.append(entry)
        return payloads

    def build_project_lookup(self) -> Dict[str, Dict[str, Any]]:
        lookup: Dict[str, Dict[str, Any]] = {}
        for payload in self._get_projects_json():
            name = payload["name"]
            lookup[name.lower()] = payload
        return lookup

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get a project by ID.

        :param project_id: Project UUID
        :return: Project details
        """
        return self._request("GET", f"datastar/projects/{project_id}")

    def create_project(self, name: str, description: Optional[str] = None) -> str:
        """
        Create a new project.

        :param name: Project name
        :param description: Project description (optional)
        :return: Created project details
        """
        data = {"name": name}
        if description:
            data["description"] = description

        response = self._request("POST", "datastar/projects", data=data)

        return response["id"]

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Update a project.

        :param project_id: Project UUID
        :param name: New project name (optional)
        :param description: New project description (optional)
        """
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if description is not None:
            data["description"] = description

        self._request("PUT", f"datastar/projects/{project_id}", data=data)

    def delete_project(self, project_id: str) -> None:
        """
        Delete a project.

        :param project_id: Project UUID
        """
        self._request("DELETE", f"datastar/projects/{project_id}")

    # ==================== MACRO RELATED ====================

    def get_macros(self, project_id: str) -> Dict[str, Any]:
        return self._request("GET", f"datastar/projects/{project_id}/macros")

    def get_macro(self, project_id: str, macro_id: str) -> Dict[str, Any]:
        return self._request("GET", f"datastar/projects/{project_id}/macros/{macro_id}")

    def create_macro(
        self,
        project_id: str,
        name: str,
        description: str,
    ) -> str:

        payload: Dict[str, Any] = {"name": name, "description": description}

        response = self._request(
            "POST", f"datastar/projects/{project_id}/macros", data=payload
        )

        return response["item"]["id"]

    def update_macro(
        self,
        project_id: str,
        macro_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> None:
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if configuration is not None:
            data["configuration"] = configuration

        self._request(
            "PATCH", f"datastar/projects/{project_id}/macros/{macro_id}", data=data
        )

    def delete_macro(self, project_id: str, macro_id: str) -> None:
        self._request("DELETE", f"datastar/projects/{project_id}/macros/{macro_id}")

    def execute_macro(
        self,
        project_id: str,
        macro_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = parameters or {}
        return self._request(
            "POST",
            f"datastar/projects/{project_id}/macros/{macro_id}/execute",
            data=payload,
        )

    def get_macro_run(self, project_id: str, macro_run_id: str) -> Dict[str, Any]:
        return self._request(
            "GET", f"datastar/projects/{project_id}/macros/runs/{macro_run_id}"
        )

    def get_macro_runs(
        self, project_id: str, macro_id: Optional[str] = None
    ) -> Dict[str, Any]:

        # Seeing timeouts here: https://optilogic.atlassian.net/browse/DST-593

        if macro_id:
            return self._request(
                "GET", f"datastar/projects/{project_id}/macros/{macro_id}/runs"
            )

        return self._request("GET", f"datastar/projects/{project_id}/macros/runs")

    # ==================== TASK RELATED ====================

    def get_tasks(self, project_id: str, macro_id: str) -> Dict[str, Any]:
        """
        Get all tasks for a macro.

        :param project_id: Project UUID
        :param macro_id: Macro UUID
        :return: Dictionary containing list of tasks
        """
        return self._request(
            "GET", f"datastar/projects/{project_id}/macros/{macro_id}/tasks"
        )

    def get_task(self, project_id: str, macro_id: str, task_id: str) -> Dict[str, Any]:
        """
        Get a task by ID.

        :param project_id: Project UUID
        :param macro_id: Macro UUID
        :param task_id: Task UUID
        :return: Task details
        """
        return self._request("GET", f"datastar/projects/{project_id}/tasks/{task_id}")

    def create_task(
        self,
        project_id: str,
        macro_id: str,
        name: str,
        task_type: str,
        configuration: Dict[str, Any],
        description: Optional[str] = None,
        ui_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task.

        :param project_id: Project UUID
        :param macro_id: Macro UUID
        :param name: Task name
        :param task_type: Type of task
        :param configuration: Task configuration
        :param description: Task description (optional)
        :param ui_metadata: UI metadata for the task (optional)
        :return: Created task details
        """
        data: Dict[str, Any] = {
            "name": name,
            "taskType": task_type,
            "configuration": configuration,
        }
        if description is not None:
            data["description"] = description
        if ui_metadata is not None:
            data["uiMetadata"] = ui_metadata

        return self._request(
            "POST", f"datastar/projects/{project_id}/macros/{macro_id}/tasks", data=data
        )

    def update_task(
        self,
        project_id: str,
        task_id: str,
        name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ui_metadata: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> None:
        """
        Update a task.

        :param project_id: Project UUID
        :param task_id: Task UUID
        :param name: New task name (optional)
        :param configuration: New task configuration (optional)
        :param description: New task description (optional)
        :param ui_metadata: UI metadata for the task (optional)
        :param status: Task status (optional)
        """
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if configuration:
            data["configuration"] = configuration
        if description is not None:
            data["description"] = description
        if ui_metadata is not None:
            data["uiMetadata"] = ui_metadata
        if status is not None:
            data["status"] = status

        self._request(
            "PATCH", f"datastar/projects/{project_id}/tasks/{task_id}", data=data
        )

    def delete_task(self, project_id: str, task_id: str) -> None:
        """
        Delete a task.

        :param project_id: Project UUID
        :param task_id: Task UUID
        """
        self._request("DELETE", f"datastar/projects/{project_id}/tasks/{task_id}")

    def get_task_types(self, include_unsupported: bool = False) -> Dict[str, Any]:
        """
        Get available task types.

        :param include_unsupported: If True, includes unsupported task types; otherwise only supported types are returned
        :return: List of task type dictionaries
        """
        params = {"includeUnsupported": str(include_unsupported).lower()}
        return self._request("GET", "datastar/tasks/types", params=params)

    def get_task_dependencies(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """
        Get task dependencies for a task.

        :param project_id: Project UUID
        :param task_id: Task UUID
        :return: Dictionary containing task dependencies
        """
        return self._request(
            "GET", f"datastar/projects/{project_id}/tasks/{task_id}/dependencies"
        )

    def create_task_dependency(
        self, project_id: str, task_id: str, dependency_task_id: str
    ) -> Dict[str, Any]:
        """
        Create a task dependency.

        :param project_id: Project UUID
        :param task_id: Task UUID (the task that depends on another)
        :param dependency_task_id: UUID of the task that this task depends on
        :param configuration: Dependency configuration (optional)
        :param ui_metadata: UI metadata for the dependency edge (optional)
        :return: Created dependency details
        """
        data: Dict[str, Any] = {
            "dependencyTaskId": dependency_task_id,
        }

        return self._request(
            "POST",
            f"datastar/projects/{project_id}/tasks/{task_id}/dependencies",
            data=data,
        )

    def delete_task_dependency(
        self, project_id: str, task_dependency_id: str
    ) -> Dict[str, Any]:
        """
        Delete a task dependency.

        :param project_id: Project UUID
        :param task_dependency_id: Task dependency UUID
        :return: Deletion confirmation
        """
        return self._request(
            "DELETE",
            f"datastar/projects/{project_id}/tasks/dependencies/{task_dependency_id}",
        )

    # ==================== CONNECTION RELATED ====================

    def get_connections(self, project_id: str) -> Dict[str, Any]:
        """
        Get all connections for a project.

        :param project_id: Project UUID
        :return: Dictionary containing list of connections
        """
        return self._request("GET", f"datastar/projects/{project_id}/connectors")

    def get_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Get a connection by ID.

        :param connection_id: Connection UUID
        :return: Connection details
        """
        return self._request("GET", f"datastar/connectors/{connection_id}")

    def create_connection(
        self,
        name: str,
        connection_type: str,
        configuration: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new connection.

        :param name: Connection name
        :param connection_type: Type of connection
        :param configuration: Connection configuration
        :param description: Connection description (optional)
        :return: Created connection details
        """
        payload: Dict[str, Any] = {
            "name": name,
            "type": connection_type,
        }
        if description:
            payload["description"] = description
        payload.update(configuration or {})

        return self._request("POST", "datastar/connectors", data=payload)

    def update_connection(
        self,
        connection_id: str,
        name: Optional[str] = None,
        connection_type: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Update a connection.

        :param connection_id: Connection UUID
        :param name: New connection name (optional)
        :param connection_type: New connection type (optional)
        :param configuration: New connection configuration (optional)
        :param description: New connection description (optional)
        """
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if connection_type:
            data["type"] = connection_type
        if configuration:
            data.update(configuration)
        if description is not None:
            data["description"] = description

        self._request("PUT", f"datastar/connectors/{connection_id}", data=data)

    def delete_connection(self, connection_id: str) -> None:
        """
        Delete a connection.

        :param connection_id: Connection UUID
        """
        self._request("DELETE", f"datastar/connectors/{connection_id}")

    def get_connectors(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page

        return self._request("GET", "datastar/connectors", params=params)

    def get_connector_types(self) -> Dict[str, Any]:
        """
        Get available connector types.

        :return: Connector type definitions keyed by connector family
        """
        return self._request("GET", "datastar/connectors/types")

    def get_connector(self, connector_id: str) -> Dict[str, Any]:
        return self._request("GET", f"datastar/connectors/{connector_id}")

    def create_connector(self, connector_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "datastar/connectors", data=connector_data)

    def update_connector(
        self, connector_id: str, connector_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request(
            "PUT", f"datastar/connectors/{connector_id}", data=connector_data
        )

    def delete_connector(self, connector_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"datastar/connectors/{connector_id}")

    def get_connector_tables(
        self, connector_id: str, project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if project_id:
            params["projectId"] = project_id
        return self._request(
            "GET", f"datastar/connectors/{connector_id}/tables", params=params
        )

    def get_connector_schema(
        self, connector_id: str, table: Optional[str] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if table:
            params["table"] = table
        return self._request(
            "POST", f"datastar/connectors/{connector_id}/schema", params=params
        )

    def get_connector_schema_tree(
        self,
        connector_id: str,
        project_id: Optional[str] = None,
        depth: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if project_id:
            params["projectId"] = project_id
        if depth:
            params["depth"] = depth
        if parent_id:
            params["parentId"] = parent_id
        return self._request(
            "GET", f"datastar/connectors/{connector_id}/schema-tree", params=params
        )

    def preview_connector_data(
        self, connector_id: str, preview_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request(
            "POST", f"datastar/connectors/{connector_id}/preview", data=preview_request
        )

    def get_connector_records(
        self,
        connector_id: str,
        table: str,
        project_id: str,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        params = {"table": table, "page": page, "limit": limit, "projectId": project_id}
        return self._request(
            "GET", f"datastar/connectors/{connector_id}/records", params=params
        )

    # ==================== SANDBOX RELATED ====================

    def get_sandbox_tables(self, project_id: str) -> Dict[str, Any]:
        """
        Convenience wrapper to list tables stored in the sandbox connector.
        """
        return self.get_connector_tables(
            self.SANDBOX_CONNECTOR_ID, project_id=project_id
        )

    def get_sandbox_schema(self, table: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve schema metadata for sandbox tables.
        """
        return self.get_connector_schema(self.SANDBOX_CONNECTOR_ID, table=table)

    def get_sandbox_schema_tree(
        self,
        project_id: str,
        depth: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve sandbox schema tree using the default connector identifier.
        """
        return self.get_connector_schema_tree(
            self.SANDBOX_CONNECTOR_ID,
            project_id=project_id,
            depth=depth,
            parent_id=parent_id,
        )

    def preview_sandbox_data(self, preview_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview sandbox data using the default connector.
        """
        return self.preview_connector_data(self.SANDBOX_CONNECTOR_ID, preview_request)

    def get_sandbox_records(
        self,
        table: str,
        project_id: str,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Retrieve sandbox records with pagination parameters.
        """
        return self.get_connector_records(
            self.SANDBOX_CONNECTOR_ID,
            table=table,
            project_id=project_id,
            page=page,
            limit=limit,
        )

    # ==================== MISC ====================

    @staticmethod
    def coerce_collection(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, dict):
            for key in ("items", "data", "storages"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
                if isinstance(value, dict):
                    return [value]
            if "item" in payload and isinstance(payload["item"], dict):
                return [payload["item"]]
            return [payload]
        if isinstance(payload, list):
            return payload
        return []

    @staticmethod
    def extract_first(payload: Any) -> Dict[str, Any]:
        items = DatastarAPI.coerce_collection(payload)
        return items[0] if items else {}
