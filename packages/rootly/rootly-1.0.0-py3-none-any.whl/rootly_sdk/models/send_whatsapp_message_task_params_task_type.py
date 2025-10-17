from enum import Enum


class SendWhatsappMessageTaskParamsTaskType(str, Enum):
    SEND_WHATSAPP_MESSAGE = "send_whatsapp_message"

    def __str__(self) -> str:
        return str(self.value)
