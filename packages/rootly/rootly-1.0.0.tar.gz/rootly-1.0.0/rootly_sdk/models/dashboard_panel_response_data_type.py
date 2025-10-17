from enum import Enum


class DashboardPanelResponseDataType(str, Enum):
    DASHBOARD_PANELS = "dashboard_panels"

    def __str__(self) -> str:
        return str(self.value)
