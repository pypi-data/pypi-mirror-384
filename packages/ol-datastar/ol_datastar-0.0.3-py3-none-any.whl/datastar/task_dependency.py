from .project import Project


class TaskDependency:
    """Represents a dependency between two macro tasks."""

    def __init__(self, project: Project, data: Dict[str, Any]):
        self.project = project
        self.id = data.get("id")
        self.task_id = data.get("taskId")
        self.dependency_task_id = data.get("dependencyTaskId")
        self.configuration = data.get("configuration", {})

    def delete(self) -> None:
        return self.project.api().delete_task_dependency(self.project.id, self.id)

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"TaskDependency(id='{self.id}', task='{self.task_id}', depends_on='{self.dependency_task_id}')"

    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        project: "Project",
        task_id: str,
        dependency_task_id: str,
        *,
        configuration: Optional[Dict[str, Any]] = None,
        ui_metadata: Optional[Dict[str, Any]] = None,
    ) -> "TaskDependency":
        response = project.api().create_task_dependency(
            project.id,
            task_id,
            dependency_task_id,
            configuration=configuration,
            ui_metadata=ui_metadata,
        )
        return cls(project, DatastarAPI.extract_first(response))
