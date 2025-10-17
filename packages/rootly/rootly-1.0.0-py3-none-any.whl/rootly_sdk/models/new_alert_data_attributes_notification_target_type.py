from enum import Enum


class NewAlertDataAttributesNotificationTargetType(str, Enum):
    ESCALATIONPOLICY = "EscalationPolicy"
    GROUP = "Group"
    SERVICE = "Service"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
