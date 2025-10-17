from enum import Enum


class NewHeartbeatDataType(str, Enum):
    HEARTBEATS = "heartbeats"

    def __str__(self) -> str:
        return str(self.value)
