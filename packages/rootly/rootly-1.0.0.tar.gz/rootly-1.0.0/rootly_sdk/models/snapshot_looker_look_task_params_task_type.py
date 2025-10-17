from enum import Enum


class SnapshotLookerLookTaskParamsTaskType(str, Enum):
    SNAPSHOT_LOOKER_LOOK = "snapshot_looker_look"

    def __str__(self) -> str:
        return str(self.value)
