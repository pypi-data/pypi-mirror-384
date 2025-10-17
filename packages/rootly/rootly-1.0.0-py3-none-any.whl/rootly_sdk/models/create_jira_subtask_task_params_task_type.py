from enum import Enum


class CreateJiraSubtaskTaskParamsTaskType(str, Enum):
    CREATE_JIRA_SUBTASK = "create_jira_subtask"

    def __str__(self) -> str:
        return str(self.value)
