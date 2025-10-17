from enum import Enum


class SnapshotGrafanaDashboardTaskParamsTaskType(str, Enum):
    SNAPSHOT_GRAFANA_DASHBOARD = "snapshot_grafana_dashboard"

    def __str__(self) -> str:
        return str(self.value)
