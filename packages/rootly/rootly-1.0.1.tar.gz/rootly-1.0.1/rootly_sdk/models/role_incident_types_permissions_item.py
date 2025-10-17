from typing import Literal, cast

RoleIncidentTypesPermissionsItem = Literal["create", "delete", "read", "update"]

ROLE_INCIDENT_TYPES_PERMISSIONS_ITEM_VALUES: set[RoleIncidentTypesPermissionsItem] = {
    "create",
    "delete",
    "read",
    "update",
}


def check_role_incident_types_permissions_item(value: str) -> RoleIncidentTypesPermissionsItem:
    if value in ROLE_INCIDENT_TYPES_PERMISSIONS_ITEM_VALUES:
        return cast(RoleIncidentTypesPermissionsItem, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ROLE_INCIDENT_TYPES_PERMISSIONS_ITEM_VALUES!r}")
