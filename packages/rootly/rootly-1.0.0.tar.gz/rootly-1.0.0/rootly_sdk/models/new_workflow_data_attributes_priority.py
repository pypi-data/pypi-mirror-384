from enum import Enum


class NewWorkflowDataAttributesPriority(str, Enum):
    HIGH = "high"
    LOW = "low"
    NORMAL = "normal"

    def __str__(self) -> str:
        return str(self.value)
