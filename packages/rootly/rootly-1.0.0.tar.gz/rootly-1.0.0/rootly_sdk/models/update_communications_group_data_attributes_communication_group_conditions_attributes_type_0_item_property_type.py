from enum import Enum


class UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0ItemPropertyType(str, Enum):
    FUNCTIONALITY = "functionality"
    GROUP = "group"
    INCIDENT_TYPE = "incident_type"
    SERVICE = "service"
    SEVERITY = "severity"

    def __str__(self) -> str:
        return str(self.value)
