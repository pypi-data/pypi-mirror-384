from enum import Enum


class GetAlertsTaskParamsTaskType(str, Enum):
    GET_ALERTS = "get_alerts"

    def __str__(self) -> str:
        return str(self.value)
