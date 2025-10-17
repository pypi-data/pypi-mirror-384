from enum import Enum


class GetDashboardInclude(str, Enum):
    PANELS = "panels"

    def __str__(self) -> str:
        return str(self.value)
