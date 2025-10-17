from enum import Enum


class CommunicationsTemplateResponseDataType(str, Enum):
    COMMUNICATIONS_TEMPLATES = "communications-templates"

    def __str__(self) -> str:
        return str(self.value)
