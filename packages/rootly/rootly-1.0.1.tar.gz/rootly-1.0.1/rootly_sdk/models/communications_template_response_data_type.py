from typing import Literal, cast

CommunicationsTemplateResponseDataType = Literal["communications-templates"]

COMMUNICATIONS_TEMPLATE_RESPONSE_DATA_TYPE_VALUES: set[CommunicationsTemplateResponseDataType] = {
    "communications-templates",
}


def check_communications_template_response_data_type(value: str) -> CommunicationsTemplateResponseDataType:
    if value in COMMUNICATIONS_TEMPLATE_RESPONSE_DATA_TYPE_VALUES:
        return cast(CommunicationsTemplateResponseDataType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {COMMUNICATIONS_TEMPLATE_RESPONSE_DATA_TYPE_VALUES!r}"
    )
