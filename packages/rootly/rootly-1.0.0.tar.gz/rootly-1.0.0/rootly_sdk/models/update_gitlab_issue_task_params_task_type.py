from enum import Enum


class UpdateGitlabIssueTaskParamsTaskType(str, Enum):
    UPDATE_GITLAB_ISSUE = "update_gitlab_issue"

    def __str__(self) -> str:
        return str(self.value)
