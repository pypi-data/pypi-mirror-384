from typing import Literal, cast

RoleListDataItemType = Literal["roles"]

ROLE_LIST_DATA_ITEM_TYPE_VALUES: set[RoleListDataItemType] = {
    "roles",
}


def check_role_list_data_item_type(value: str) -> RoleListDataItemType:
    if value in ROLE_LIST_DATA_ITEM_TYPE_VALUES:
        return cast(RoleListDataItemType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ROLE_LIST_DATA_ITEM_TYPE_VALUES!r}")
