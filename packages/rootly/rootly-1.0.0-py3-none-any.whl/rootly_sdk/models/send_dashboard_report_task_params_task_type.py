from enum import Enum


class SendDashboardReportTaskParamsTaskType(str, Enum):
    SEND_DASHBOARD_REPORT = "send_dashboard_report"

    def __str__(self) -> str:
        return str(self.value)
