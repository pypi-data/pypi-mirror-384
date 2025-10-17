from enum import Enum


class CreateOpsgenieAlertTaskParamsTaskType(str, Enum):
    CREATE_OPSGENIE_ALERT = "create_opsgenie_alert"

    def __str__(self) -> str:
        return str(self.value)
