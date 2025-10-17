from enum import Enum


class WorkflowGroupListDataItemType(str, Enum):
    WORKFLOW_GROUPS = "workflow_groups"

    def __str__(self) -> str:
        return str(self.value)
