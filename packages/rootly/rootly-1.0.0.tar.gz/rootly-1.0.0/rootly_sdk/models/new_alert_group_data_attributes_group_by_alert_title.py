from enum import IntEnum


class NewAlertGroupDataAttributesGroupByAlertTitle(IntEnum):
    VALUE_1 = 1
    VALUE_0 = 0

    def __str__(self) -> str:
        return str(self.value)
