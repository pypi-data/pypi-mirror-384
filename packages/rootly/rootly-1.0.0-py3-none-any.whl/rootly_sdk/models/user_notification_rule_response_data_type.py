from enum import Enum


class UserNotificationRuleResponseDataType(str, Enum):
    USER_NOTIFICATION_RULES = "user_notification_rules"

    def __str__(self) -> str:
        return str(self.value)
