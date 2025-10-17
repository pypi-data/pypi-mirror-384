from enum import Enum


class NewHeartbeatDataAttributesNotificationTargetType(str, Enum):
    ESCALATIONPOLICY = "EscalationPolicy"
    GROUP = "Group"
    SERVICE = "Service"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
