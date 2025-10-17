from enum import Enum


class DashboardPanelParamsLegendGroups(str, Enum):
    ALL = "all"
    CHARTED = "charted"

    def __str__(self) -> str:
        return str(self.value)
