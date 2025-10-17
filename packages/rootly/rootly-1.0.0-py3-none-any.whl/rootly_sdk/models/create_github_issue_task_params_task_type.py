from enum import Enum


class CreateGithubIssueTaskParamsTaskType(str, Enum):
    CREATE_GITHUB_ISSUE = "create_github_issue"

    def __str__(self) -> str:
        return str(self.value)
