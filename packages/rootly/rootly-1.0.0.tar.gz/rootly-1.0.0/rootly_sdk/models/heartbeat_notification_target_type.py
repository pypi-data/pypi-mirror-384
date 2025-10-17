from enum import Enum


class HeartbeatNotificationTargetType(str, Enum):
    ESCALATIONPOLICY = "EscalationPolicy"
    GROUP = "Group"
    SERVICE = "Service"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
