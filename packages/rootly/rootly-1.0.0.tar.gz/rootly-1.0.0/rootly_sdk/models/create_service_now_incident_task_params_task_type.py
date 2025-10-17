from enum import Enum


class CreateServiceNowIncidentTaskParamsTaskType(str, Enum):
    CREATE_SERVICE_NOW_INCIDENT = "create_service_now_incident"

    def __str__(self) -> str:
        return str(self.value)
