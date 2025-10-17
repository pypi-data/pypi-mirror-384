from enum import Enum


class UpdateCommunicationsTemplateDataType(str, Enum):
    COMMUNICATIONS_TEMPLATES = "communications-templates"

    def __str__(self) -> str:
        return str(self.value)
