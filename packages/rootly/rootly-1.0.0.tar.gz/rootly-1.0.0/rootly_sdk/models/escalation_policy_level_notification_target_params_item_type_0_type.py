from enum import Enum


class EscalationPolicyLevelNotificationTargetParamsItemType0Type(str, Enum):
    SCHEDULE = "schedule"
    SERVICE = "service"
    SLACK_CHANNEL = "slack_channel"
    TEAM = "team"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
