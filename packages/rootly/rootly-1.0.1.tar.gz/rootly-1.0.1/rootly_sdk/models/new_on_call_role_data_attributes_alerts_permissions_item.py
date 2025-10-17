from typing import Literal, cast

NewOnCallRoleDataAttributesAlertsPermissionsItem = Literal["create", "read", "update"]

NEW_ON_CALL_ROLE_DATA_ATTRIBUTES_ALERTS_PERMISSIONS_ITEM_VALUES: set[
    NewOnCallRoleDataAttributesAlertsPermissionsItem
] = {
    "create",
    "read",
    "update",
}


def check_new_on_call_role_data_attributes_alerts_permissions_item(
    value: str,
) -> NewOnCallRoleDataAttributesAlertsPermissionsItem:
    if value in NEW_ON_CALL_ROLE_DATA_ATTRIBUTES_ALERTS_PERMISSIONS_ITEM_VALUES:
        return cast(NewOnCallRoleDataAttributesAlertsPermissionsItem, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {NEW_ON_CALL_ROLE_DATA_ATTRIBUTES_ALERTS_PERMISSIONS_ITEM_VALUES!r}"
    )
