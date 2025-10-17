from enum import Enum


class UpdateWorkflowGroupDataType(str, Enum):
    WORKFLOW_GROUPS = "workflow_groups"

    def __str__(self) -> str:
        return str(self.value)
