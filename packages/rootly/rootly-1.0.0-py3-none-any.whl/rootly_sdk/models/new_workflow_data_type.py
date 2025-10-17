from enum import Enum


class NewWorkflowDataType(str, Enum):
    WORKFLOWS = "workflows"

    def __str__(self) -> str:
        return str(self.value)
