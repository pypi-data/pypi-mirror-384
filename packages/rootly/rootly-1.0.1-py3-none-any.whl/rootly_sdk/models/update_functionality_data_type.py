from typing import Literal, cast

UpdateFunctionalityDataType = Literal["functionalities"]

UPDATE_FUNCTIONALITY_DATA_TYPE_VALUES: set[UpdateFunctionalityDataType] = {
    "functionalities",
}


def check_update_functionality_data_type(value: str) -> UpdateFunctionalityDataType:
    if value in UPDATE_FUNCTIONALITY_DATA_TYPE_VALUES:
        return cast(UpdateFunctionalityDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_FUNCTIONALITY_DATA_TYPE_VALUES!r}")
