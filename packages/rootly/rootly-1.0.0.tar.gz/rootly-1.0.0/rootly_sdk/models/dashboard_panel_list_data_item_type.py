from enum import Enum


class DashboardPanelListDataItemType(str, Enum):
    DASHBOARD_PANELS = "dashboard_panels"

    def __str__(self) -> str:
        return str(self.value)
