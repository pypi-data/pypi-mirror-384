from enum import Enum


class PublishIncidentTaskParamsTaskType(str, Enum):
    PUBLISH_INCIDENT = "publish_incident"

    def __str__(self) -> str:
        return str(self.value)
