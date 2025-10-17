from enum import Enum


class GetWorkflowInclude(str, Enum):
    FORM_FIELD_CONDITIONS = "form_field_conditions"
    GENIUS_TASKS = "genius_tasks"
    GENIUS_WORKFLOW_RUNS = "genius_workflow_runs"

    def __str__(self) -> str:
        return str(self.value)
