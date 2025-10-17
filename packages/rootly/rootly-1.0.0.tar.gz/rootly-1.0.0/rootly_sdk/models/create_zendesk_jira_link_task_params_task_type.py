from enum import Enum


class CreateZendeskJiraLinkTaskParamsTaskType(str, Enum):
    CREATE_ZENDESK_JIRA_LINK = "create_zendesk_jira_link"

    def __str__(self) -> str:
        return str(self.value)
