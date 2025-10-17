from enum import Enum


class NewStatusPageTemplateDataType(str, Enum):
    STATUS_PAGE_TEMPLATES = "status_page_templates"

    def __str__(self) -> str:
        return str(self.value)
