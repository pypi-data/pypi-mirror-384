from enum import Enum


class IncidentCustomFieldSelectionResponseDataType(str, Enum):
    INCIDENT_CUSTOM_FIELD_SELECTIONS = "incident_custom_field_selections"

    def __str__(self) -> str:
        return str(self.value)
