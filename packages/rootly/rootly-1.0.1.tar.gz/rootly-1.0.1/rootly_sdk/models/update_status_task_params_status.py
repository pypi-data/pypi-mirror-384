from typing import Literal, cast

UpdateStatusTaskParamsStatus = Literal["cancelled", "closed", "in_triage", "mitigated", "resolved", "started"]

UPDATE_STATUS_TASK_PARAMS_STATUS_VALUES: set[UpdateStatusTaskParamsStatus] = {
    "cancelled",
    "closed",
    "in_triage",
    "mitigated",
    "resolved",
    "started",
}


def check_update_status_task_params_status(value: str) -> UpdateStatusTaskParamsStatus:
    if value in UPDATE_STATUS_TASK_PARAMS_STATUS_VALUES:
        return cast(UpdateStatusTaskParamsStatus, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_STATUS_TASK_PARAMS_STATUS_VALUES!r}")
