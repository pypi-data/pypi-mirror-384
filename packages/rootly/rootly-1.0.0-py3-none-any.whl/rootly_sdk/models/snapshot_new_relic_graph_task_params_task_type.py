from enum import Enum


class SnapshotNewRelicGraphTaskParamsTaskType(str, Enum):
    SNAPSHOT_LOOKER_GRAPH = "snapshot_looker_graph"

    def __str__(self) -> str:
        return str(self.value)
