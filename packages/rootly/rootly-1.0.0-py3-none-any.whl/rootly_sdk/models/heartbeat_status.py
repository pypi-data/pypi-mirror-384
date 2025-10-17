from enum import Enum


class HeartbeatStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    WAITING = "waiting"

    def __str__(self) -> str:
        return str(self.value)
