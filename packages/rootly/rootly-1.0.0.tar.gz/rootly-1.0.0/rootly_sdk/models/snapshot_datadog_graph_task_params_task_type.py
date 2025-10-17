from enum import Enum


class SnapshotDatadogGraphTaskParamsTaskType(str, Enum):
    SNAPSHOT_DATADOG_GRAPH = "snapshot_datadog_graph"

    def __str__(self) -> str:
        return str(self.value)
