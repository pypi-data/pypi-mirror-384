from enum import Enum


class NewDashboardPanelDataType(str, Enum):
    DASHBOARD_PANELS = "dashboard_panels"

    def __str__(self) -> str:
        return str(self.value)
