from enum import Enum


class NewUserNotificationRuleDataType(str, Enum):
    USER_NOTIFICATION_RULES = "user_notification_rules"

    def __str__(self) -> str:
        return str(self.value)
