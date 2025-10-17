from typing import Literal, cast

CommunicationsTemplatesResponseDataItemType = Literal["communications-templates"]

COMMUNICATIONS_TEMPLATES_RESPONSE_DATA_ITEM_TYPE_VALUES: set[CommunicationsTemplatesResponseDataItemType] = {
    "communications-templates",
}


def check_communications_templates_response_data_item_type(value: str) -> CommunicationsTemplatesResponseDataItemType:
    if value in COMMUNICATIONS_TEMPLATES_RESPONSE_DATA_ITEM_TYPE_VALUES:
        return cast(CommunicationsTemplatesResponseDataItemType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {COMMUNICATIONS_TEMPLATES_RESPONSE_DATA_ITEM_TYPE_VALUES!r}"
    )
