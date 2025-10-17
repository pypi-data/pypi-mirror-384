from enum import Enum


class UpdateJiraIssueTaskParamsTaskType(str, Enum):
    UPDATE_JIRA_ISSUE = "update_jira_issue"

    def __str__(self) -> str:
        return str(self.value)
