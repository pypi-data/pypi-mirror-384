from enum import Enum


class UpdateGitlabIssueTaskParamsIssueType(str, Enum):
    INCIDENT = "incident"
    ISSUE = "issue"
    TASK = "task"
    TEST_CASE = "test_case"

    def __str__(self) -> str:
        return str(self.value)
