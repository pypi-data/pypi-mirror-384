from enum import Enum


class CreateZendeskTicketTaskParamsTaskType(str, Enum):
    CREATE_ZENDESK_TICKET = "create_zendesk_ticket"

    def __str__(self) -> str:
        return str(self.value)
