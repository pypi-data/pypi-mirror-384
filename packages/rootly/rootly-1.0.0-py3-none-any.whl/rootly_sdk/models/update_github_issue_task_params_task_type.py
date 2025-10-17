from enum import Enum


class UpdateGithubIssueTaskParamsTaskType(str, Enum):
    UPDATE_GITHUB_ISSUE = "update_github_issue"

    def __str__(self) -> str:
        return str(self.value)
