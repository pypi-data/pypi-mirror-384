from enum import Enum


class NewDashboardDataType(str, Enum):
    DASHBOARDS = "dashboards"

    def __str__(self) -> str:
        return str(self.value)
