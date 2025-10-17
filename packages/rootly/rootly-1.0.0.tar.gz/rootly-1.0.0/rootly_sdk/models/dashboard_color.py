from enum import Enum


class DashboardColor(str, Enum):
    VALUE_0 = "#FCF2CF"
    VALUE_1 = "#D7F5E1"
    VALUE_2 = "#E9E2FF"
    VALUE_3 = "#FAE6E8"
    VALUE_4 = "#FAEEE6"

    def __str__(self) -> str:
        return str(self.value)
