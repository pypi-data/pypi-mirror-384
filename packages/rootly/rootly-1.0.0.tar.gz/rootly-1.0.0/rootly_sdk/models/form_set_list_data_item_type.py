from enum import Enum


class FormSetListDataItemType(str, Enum):
    FORM_SETS = "form_sets"

    def __str__(self) -> str:
        return str(self.value)
