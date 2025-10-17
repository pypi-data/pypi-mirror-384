from enum import Enum


class NewIncidentTypeDataType(str, Enum):
    INCIDENT_TYPES = "incident_types"

    def __str__(self) -> str:
        return str(self.value)
