from enum import Enum


class WorkflowListDataItemType(str, Enum):
    WORKFLOWS = "workflows"

    def __str__(self) -> str:
        return str(self.value)
