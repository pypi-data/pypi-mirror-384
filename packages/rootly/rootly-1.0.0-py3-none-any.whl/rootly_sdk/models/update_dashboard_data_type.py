from enum import Enum


class UpdateDashboardDataType(str, Enum):
    DASHBOARDS = "dashboards"

    def __str__(self) -> str:
        return str(self.value)
