from enum import Enum


class SendSmsTaskParamsTaskType(str, Enum):
    SEND_SMS = "send_sms"

    def __str__(self) -> str:
        return str(self.value)
