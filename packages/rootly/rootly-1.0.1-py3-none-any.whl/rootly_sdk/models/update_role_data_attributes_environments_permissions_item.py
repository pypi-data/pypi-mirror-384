from typing import Literal, cast

UpdateRoleDataAttributesEnvironmentsPermissionsItem = Literal["create", "delete", "read", "update"]

UPDATE_ROLE_DATA_ATTRIBUTES_ENVIRONMENTS_PERMISSIONS_ITEM_VALUES: set[
    UpdateRoleDataAttributesEnvironmentsPermissionsItem
] = {
    "create",
    "delete",
    "read",
    "update",
}


def check_update_role_data_attributes_environments_permissions_item(
    value: str,
) -> UpdateRoleDataAttributesEnvironmentsPermissionsItem:
    if value in UPDATE_ROLE_DATA_ATTRIBUTES_ENVIRONMENTS_PERMISSIONS_ITEM_VALUES:
        return cast(UpdateRoleDataAttributesEnvironmentsPermissionsItem, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_ROLE_DATA_ATTRIBUTES_ENVIRONMENTS_PERMISSIONS_ITEM_VALUES!r}"
    )
