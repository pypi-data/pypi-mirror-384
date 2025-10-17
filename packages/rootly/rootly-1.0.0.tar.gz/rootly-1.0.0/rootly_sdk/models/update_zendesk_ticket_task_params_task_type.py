from enum import Enum


class UpdateZendeskTicketTaskParamsTaskType(str, Enum):
    UPDATE_ZENDESK_TICKET = "update_zendesk_ticket"

    def __str__(self) -> str:
        return str(self.value)
