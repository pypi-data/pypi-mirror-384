from enum import Enum


class PostMortemTemplateFormat(str, Enum):
    HTML = "html"
    MARKDOWN = "markdown"

    def __str__(self) -> str:
        return str(self.value)
