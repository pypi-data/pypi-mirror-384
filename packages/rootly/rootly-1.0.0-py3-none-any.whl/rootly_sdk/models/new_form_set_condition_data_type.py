from enum import Enum


class NewFormSetConditionDataType(str, Enum):
    FORM_SET_CONDITIONS = "form_set_conditions"

    def __str__(self) -> str:
        return str(self.value)
