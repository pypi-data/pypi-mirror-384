from enum import Enum


class UpdateWorkflowDataType(str, Enum):
    WORKFLOWS = "workflows"

    def __str__(self) -> str:
        return str(self.value)
