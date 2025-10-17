from typing import Literal, cast

NewSeverityDataType = Literal["severities"]

NEW_SEVERITY_DATA_TYPE_VALUES: set[NewSeverityDataType] = {
    "severities",
}


def check_new_severity_data_type(value: str) -> NewSeverityDataType:
    if value in NEW_SEVERITY_DATA_TYPE_VALUES:
        return cast(NewSeverityDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {NEW_SEVERITY_DATA_TYPE_VALUES!r}")
