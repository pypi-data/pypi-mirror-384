from typing import Literal, cast

UpdateOnCallRoleDataAttributesSchedulesPermissionsItem = Literal["create", "delete", "read", "update"]

UPDATE_ON_CALL_ROLE_DATA_ATTRIBUTES_SCHEDULES_PERMISSIONS_ITEM_VALUES: set[
    UpdateOnCallRoleDataAttributesSchedulesPermissionsItem
] = {
    "create",
    "delete",
    "read",
    "update",
}


def check_update_on_call_role_data_attributes_schedules_permissions_item(
    value: str,
) -> UpdateOnCallRoleDataAttributesSchedulesPermissionsItem:
    if value in UPDATE_ON_CALL_ROLE_DATA_ATTRIBUTES_SCHEDULES_PERMISSIONS_ITEM_VALUES:
        return cast(UpdateOnCallRoleDataAttributesSchedulesPermissionsItem, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_ON_CALL_ROLE_DATA_ATTRIBUTES_SCHEDULES_PERMISSIONS_ITEM_VALUES!r}"
    )
