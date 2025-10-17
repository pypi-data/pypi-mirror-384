from enum import Enum


class ListDashboardsInclude(str, Enum):
    PANELS = "panels"

    def __str__(self) -> str:
        return str(self.value)
