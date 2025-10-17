from typing import Literal, cast

RolePlaybooksPermissionsItem = Literal["create", "delete", "read", "update"]

ROLE_PLAYBOOKS_PERMISSIONS_ITEM_VALUES: set[RolePlaybooksPermissionsItem] = {
    "create",
    "delete",
    "read",
    "update",
}


def check_role_playbooks_permissions_item(value: str) -> RolePlaybooksPermissionsItem:
    if value in ROLE_PLAYBOOKS_PERMISSIONS_ITEM_VALUES:
        return cast(RolePlaybooksPermissionsItem, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ROLE_PLAYBOOKS_PERMISSIONS_ITEM_VALUES!r}")
