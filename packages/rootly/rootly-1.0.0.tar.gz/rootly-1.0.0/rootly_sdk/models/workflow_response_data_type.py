from enum import Enum


class WorkflowResponseDataType(str, Enum):
    WORKFLOWS = "workflows"

    def __str__(self) -> str:
        return str(self.value)
