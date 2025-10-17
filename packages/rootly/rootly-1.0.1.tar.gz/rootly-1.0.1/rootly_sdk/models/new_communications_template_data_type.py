from typing import Literal, cast

NewCommunicationsTemplateDataType = Literal["communications-templates"]

NEW_COMMUNICATIONS_TEMPLATE_DATA_TYPE_VALUES: set[NewCommunicationsTemplateDataType] = {
    "communications-templates",
}


def check_new_communications_template_data_type(value: str) -> NewCommunicationsTemplateDataType:
    if value in NEW_COMMUNICATIONS_TEMPLATE_DATA_TYPE_VALUES:
        return cast(NewCommunicationsTemplateDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {NEW_COMMUNICATIONS_TEMPLATE_DATA_TYPE_VALUES!r}")
