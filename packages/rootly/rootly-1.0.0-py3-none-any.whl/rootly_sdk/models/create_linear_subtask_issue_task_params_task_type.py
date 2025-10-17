from enum import Enum


class CreateLinearSubtaskIssueTaskParamsTaskType(str, Enum):
    CREATE_LINEAR_SUBTASK_ISSUE = "create_linear_subtask_issue"

    def __str__(self) -> str:
        return str(self.value)
