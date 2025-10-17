from enum import Enum


class TriggerWorkflowTaskParamsTaskType(str, Enum):
    TRIGGER_WORKFLOW = "trigger_workflow"

    def __str__(self) -> str:
        return str(self.value)
