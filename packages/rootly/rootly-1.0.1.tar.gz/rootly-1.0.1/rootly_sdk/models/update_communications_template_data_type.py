from typing import Literal, cast

UpdateCommunicationsTemplateDataType = Literal["communications-templates"]

UPDATE_COMMUNICATIONS_TEMPLATE_DATA_TYPE_VALUES: set[UpdateCommunicationsTemplateDataType] = {
    "communications-templates",
}


def check_update_communications_template_data_type(value: str) -> UpdateCommunicationsTemplateDataType:
    if value in UPDATE_COMMUNICATIONS_TEMPLATE_DATA_TYPE_VALUES:
        return cast(UpdateCommunicationsTemplateDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_COMMUNICATIONS_TEMPLATE_DATA_TYPE_VALUES!r}")
