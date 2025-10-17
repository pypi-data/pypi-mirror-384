from enum import Enum


class NewUserNotificationRuleDataAttributesEnabledContactTypesItem(str, Enum):
    CALL = "call"
    DEVICE = "device"
    EMAIL = "email"
    NON_CRITICAL_DEVICE = "non_critical_device"
    SMS = "sms"

    def __str__(self) -> str:
        return str(self.value)
