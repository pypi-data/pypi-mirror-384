from enum import Enum


class CreateDatadogNotebookTaskParamsKind(str, Enum):
    DOCUMENTATION = "documentation"
    INVESTIGATION = "investigation"
    POSTMORTEM = "postmortem"
    REPORT = "report"
    RUNBOOK = "runbook"

    def __str__(self) -> str:
        return str(self.value)
