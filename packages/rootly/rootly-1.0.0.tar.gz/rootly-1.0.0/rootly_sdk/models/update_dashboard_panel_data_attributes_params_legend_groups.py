from enum import Enum


class UpdateDashboardPanelDataAttributesParamsLegendGroups(str, Enum):
    ALL = "all"
    CHARTED = "charted"

    def __str__(self) -> str:
        return str(self.value)
