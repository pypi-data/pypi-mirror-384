from enum import Enum


class UpdateOpsgenieAlertTaskParamsTaskType(str, Enum):
    UPDATE_OPSGENIE_ALERT = "update_opsgenie_alert"

    def __str__(self) -> str:
        return str(self.value)
