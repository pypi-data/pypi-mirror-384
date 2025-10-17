from enum import Enum


class UpdateFormFieldDataAttributesInputKind(str, Enum):
    CHECKBOX = "checkbox"
    DATE = "date"
    DATETIME = "datetime"
    MULTI_SELECT = "multi_select"
    NUMBER = "number"
    RICH_TEXT = "rich_text"
    SELECT = "select"
    TAGS = "tags"
    TEXT = "text"
    TEXTAREA = "textarea"

    def __str__(self) -> str:
        return str(self.value)
