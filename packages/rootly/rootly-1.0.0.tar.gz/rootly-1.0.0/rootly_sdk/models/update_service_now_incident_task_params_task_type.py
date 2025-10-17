from enum import Enum


class UpdateServiceNowIncidentTaskParamsTaskType(str, Enum):
    UPDATE_SERVICE_NOW_INCIDENT = "update_service_now_incident"

    def __str__(self) -> str:
        return str(self.value)
