from typing import Literal, cast

CommunicationsGroupsResponseDataItemType = Literal["communications-groups"]

COMMUNICATIONS_GROUPS_RESPONSE_DATA_ITEM_TYPE_VALUES: set[CommunicationsGroupsResponseDataItemType] = {
    "communications-groups",
}


def check_communications_groups_response_data_item_type(value: str) -> CommunicationsGroupsResponseDataItemType:
    if value in COMMUNICATIONS_GROUPS_RESPONSE_DATA_ITEM_TYPE_VALUES:
        return cast(CommunicationsGroupsResponseDataItemType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {COMMUNICATIONS_GROUPS_RESPONSE_DATA_ITEM_TYPE_VALUES!r}"
    )
