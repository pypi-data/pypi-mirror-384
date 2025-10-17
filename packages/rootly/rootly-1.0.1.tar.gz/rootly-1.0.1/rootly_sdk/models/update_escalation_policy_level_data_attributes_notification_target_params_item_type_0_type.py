from typing import Literal, cast

UpdateEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type = Literal[
    "schedule", "service", "slack_channel", "team", "user"
]

UPDATE_ESCALATION_POLICY_LEVEL_DATA_ATTRIBUTES_NOTIFICATION_TARGET_PARAMS_ITEM_TYPE_0_TYPE_VALUES: set[
    UpdateEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type
] = {
    "schedule",
    "service",
    "slack_channel",
    "team",
    "user",
}


def check_update_escalation_policy_level_data_attributes_notification_target_params_item_type_0_type(
    value: str,
) -> UpdateEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type:
    if value in UPDATE_ESCALATION_POLICY_LEVEL_DATA_ATTRIBUTES_NOTIFICATION_TARGET_PARAMS_ITEM_TYPE_0_TYPE_VALUES:
        return cast(UpdateEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_ESCALATION_POLICY_LEVEL_DATA_ATTRIBUTES_NOTIFICATION_TARGET_PARAMS_ITEM_TYPE_0_TYPE_VALUES!r}"
    )
