from enum import Enum


class CreateJiraIssueTaskParamsTaskType(str, Enum):
    CREATE_JIRA_ISSUE = "create_jira_issue"

    def __str__(self) -> str:
        return str(self.value)
