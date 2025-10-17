from enum import Enum


class CreateLinearIssueTaskParamsTaskType(str, Enum):
    CREATE_LINEAR_ISSUE = "create_linear_issue"

    def __str__(self) -> str:
        return str(self.value)
