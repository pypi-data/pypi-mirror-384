from typing import Literal, cast

NewCustomFieldOptionDataType = Literal["custom_field_options"]

NEW_CUSTOM_FIELD_OPTION_DATA_TYPE_VALUES: set[NewCustomFieldOptionDataType] = {
    "custom_field_options",
}


def check_new_custom_field_option_data_type(value: str) -> NewCustomFieldOptionDataType:
    if value in NEW_CUSTOM_FIELD_OPTION_DATA_TYPE_VALUES:
        return cast(NewCustomFieldOptionDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {NEW_CUSTOM_FIELD_OPTION_DATA_TYPE_VALUES!r}")
