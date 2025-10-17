from enum import Enum


class AddActionItemTaskParamsAttributeToQueryBy(str, Enum):
    JIRA_ISSUE_ID = "jira_issue_id"

    def __str__(self) -> str:
        return str(self.value)
