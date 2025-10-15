"""Task type for start task."""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from ..task import Task

if TYPE_CHECKING:
    from ..macro import Macro


class StartTask(Task):
    """Start is a special placeholder task at the beginning of a Macro."""

    # TODO: could take id, name, description, ui meta and so on here, but does it need prevent
    # task.delete , update etc?

    def __init__(
        self,
        macro: "Macro",
    ) -> None:

        super().__init__(
            task_id="NA", macro=macro, name="Start", description="Start Task"
        )

    # ------------------------------------------------------------------
    # Abstract method implementation

    def get_task_type(self) -> str:
        return "start"

    def _to_configuration(self) -> Dict[str, Any]:
        return {}

    def _from_configuration(self, configuration: Dict[str, Any]) -> None:
        pass
