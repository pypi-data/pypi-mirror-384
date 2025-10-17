from enum import Enum


class CreateGitlabIssueTaskParamsTaskType(str, Enum):
    CREATE_GITLAB_ISSUE = "create_gitlab_issue"

    def __str__(self) -> str:
        return str(self.value)
