from enum import Enum


class NewFormSetDataType(str, Enum):
    FORM_SETS = "form_sets"

    def __str__(self) -> str:
        return str(self.value)
