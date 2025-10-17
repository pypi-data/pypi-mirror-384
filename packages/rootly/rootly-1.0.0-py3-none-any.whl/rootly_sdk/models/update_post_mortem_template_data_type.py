from enum import Enum


class UpdatePostMortemTemplateDataType(str, Enum):
    POST_MORTEM_TEMPLATES = "post_mortem_templates"

    def __str__(self) -> str:
        return str(self.value)
