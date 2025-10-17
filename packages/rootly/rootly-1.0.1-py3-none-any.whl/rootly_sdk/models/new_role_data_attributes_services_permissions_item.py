from typing import Literal, cast

NewRoleDataAttributesServicesPermissionsItem = Literal["create", "delete", "read", "update"]

NEW_ROLE_DATA_ATTRIBUTES_SERVICES_PERMISSIONS_ITEM_VALUES: set[NewRoleDataAttributesServicesPermissionsItem] = {
    "create",
    "delete",
    "read",
    "update",
}


def check_new_role_data_attributes_services_permissions_item(
    value: str,
) -> NewRoleDataAttributesServicesPermissionsItem:
    if value in NEW_ROLE_DATA_ATTRIBUTES_SERVICES_PERMISSIONS_ITEM_VALUES:
        return cast(NewRoleDataAttributesServicesPermissionsItem, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {NEW_ROLE_DATA_ATTRIBUTES_SERVICES_PERMISSIONS_ITEM_VALUES!r}"
    )
