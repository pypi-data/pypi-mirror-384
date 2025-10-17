from enum import Enum


class CreateLinearIssueCommentTaskParamsTaskType(str, Enum):
    CREATE_LINEAR_ISSUE_COMMENT = "create_linear_issue_comment"

    def __str__(self) -> str:
        return str(self.value)
