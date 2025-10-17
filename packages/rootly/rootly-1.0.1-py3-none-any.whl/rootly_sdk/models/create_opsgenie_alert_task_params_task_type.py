from typing import Literal, cast

CreateOpsgenieAlertTaskParamsTaskType = Literal["create_opsgenie_alert"]

CREATE_OPSGENIE_ALERT_TASK_PARAMS_TASK_TYPE_VALUES: set[CreateOpsgenieAlertTaskParamsTaskType] = {
    "create_opsgenie_alert",
}


def check_create_opsgenie_alert_task_params_task_type(value: str) -> CreateOpsgenieAlertTaskParamsTaskType:
    if value in CREATE_OPSGENIE_ALERT_TASK_PARAMS_TASK_TYPE_VALUES:
        return cast(CreateOpsgenieAlertTaskParamsTaskType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {CREATE_OPSGENIE_ALERT_TASK_PARAMS_TASK_TYPE_VALUES!r}"
    )
