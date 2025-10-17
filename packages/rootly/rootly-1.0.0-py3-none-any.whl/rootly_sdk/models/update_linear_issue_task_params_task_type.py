from enum import Enum


class UpdateLinearIssueTaskParamsTaskType(str, Enum):
    UPDATE_LINEAR_ISSUE = "update_linear_issue"

    def __str__(self) -> str:
        return str(self.value)
