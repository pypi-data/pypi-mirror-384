from enum import Enum


class CreateZendeskTicketTaskParamsKind(str, Enum):
    INCIDENT = "incident"
    PROBLEM = "problem"
    QUESTION = "question"
    TASK = "task"

    def __str__(self) -> str:
        return str(self.value)
