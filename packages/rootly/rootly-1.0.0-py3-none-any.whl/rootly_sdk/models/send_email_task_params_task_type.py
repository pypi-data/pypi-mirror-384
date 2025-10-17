from enum import Enum


class SendEmailTaskParamsTaskType(str, Enum):
    SEND_EMAIL = "send_email"

    def __str__(self) -> str:
        return str(self.value)
