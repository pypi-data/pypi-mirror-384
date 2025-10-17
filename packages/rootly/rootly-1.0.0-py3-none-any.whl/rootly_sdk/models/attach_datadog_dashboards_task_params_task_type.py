from enum import Enum


class AttachDatadogDashboardsTaskParamsTaskType(str, Enum):
    ATTACH_DATADOG_DASHBOARDS = "attach_datadog_dashboards"

    def __str__(self) -> str:
        return str(self.value)
