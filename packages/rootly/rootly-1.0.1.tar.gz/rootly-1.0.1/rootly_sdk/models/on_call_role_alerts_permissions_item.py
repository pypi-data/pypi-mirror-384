from typing import Literal, cast

OnCallRoleAlertsPermissionsItem = Literal["create", "read", "update"]

ON_CALL_ROLE_ALERTS_PERMISSIONS_ITEM_VALUES: set[OnCallRoleAlertsPermissionsItem] = {
    "create",
    "read",
    "update",
}


def check_on_call_role_alerts_permissions_item(value: str) -> OnCallRoleAlertsPermissionsItem:
    if value in ON_CALL_ROLE_ALERTS_PERMISSIONS_ITEM_VALUES:
        return cast(OnCallRoleAlertsPermissionsItem, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ON_CALL_ROLE_ALERTS_PERMISSIONS_ITEM_VALUES!r}")
