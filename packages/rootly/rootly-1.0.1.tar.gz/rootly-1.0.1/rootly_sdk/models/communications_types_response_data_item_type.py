from typing import Literal, cast

CommunicationsTypesResponseDataItemType = Literal["communications_types"]

COMMUNICATIONS_TYPES_RESPONSE_DATA_ITEM_TYPE_VALUES: set[CommunicationsTypesResponseDataItemType] = {
    "communications_types",
}


def check_communications_types_response_data_item_type(value: str) -> CommunicationsTypesResponseDataItemType:
    if value in COMMUNICATIONS_TYPES_RESPONSE_DATA_ITEM_TYPE_VALUES:
        return cast(CommunicationsTypesResponseDataItemType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {COMMUNICATIONS_TYPES_RESPONSE_DATA_ITEM_TYPE_VALUES!r}"
    )
