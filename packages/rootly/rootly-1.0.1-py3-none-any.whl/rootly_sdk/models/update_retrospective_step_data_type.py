from typing import Literal, cast

UpdateRetrospectiveStepDataType = Literal["retrospective_steps"]

UPDATE_RETROSPECTIVE_STEP_DATA_TYPE_VALUES: set[UpdateRetrospectiveStepDataType] = {
    "retrospective_steps",
}


def check_update_retrospective_step_data_type(value: str) -> UpdateRetrospectiveStepDataType:
    if value in UPDATE_RETROSPECTIVE_STEP_DATA_TYPE_VALUES:
        return cast(UpdateRetrospectiveStepDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_RETROSPECTIVE_STEP_DATA_TYPE_VALUES!r}")
