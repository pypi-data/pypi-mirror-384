from typing import Literal, cast

UserNotificationRuleEnabledContactTypesItem = Literal["call", "device", "email", "non_critical_device", "sms"]

USER_NOTIFICATION_RULE_ENABLED_CONTACT_TYPES_ITEM_VALUES: set[UserNotificationRuleEnabledContactTypesItem] = {
    "call",
    "device",
    "email",
    "non_critical_device",
    "sms",
}


def check_user_notification_rule_enabled_contact_types_item(value: str) -> UserNotificationRuleEnabledContactTypesItem:
    if value in USER_NOTIFICATION_RULE_ENABLED_CONTACT_TYPES_ITEM_VALUES:
        return cast(UserNotificationRuleEnabledContactTypesItem, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {USER_NOTIFICATION_RULE_ENABLED_CONTACT_TYPES_ITEM_VALUES!r}"
    )
