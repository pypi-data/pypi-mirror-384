from typing import Literal, cast

UpdateCommunicationsGroupDataType = Literal["communications-groups"]

UPDATE_COMMUNICATIONS_GROUP_DATA_TYPE_VALUES: set[UpdateCommunicationsGroupDataType] = {
    "communications-groups",
}


def check_update_communications_group_data_type(value: str) -> UpdateCommunicationsGroupDataType:
    if value in UPDATE_COMMUNICATIONS_GROUP_DATA_TYPE_VALUES:
        return cast(UpdateCommunicationsGroupDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_COMMUNICATIONS_GROUP_DATA_TYPE_VALUES!r}")
