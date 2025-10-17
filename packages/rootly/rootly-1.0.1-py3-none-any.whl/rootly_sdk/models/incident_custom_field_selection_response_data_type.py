from typing import Literal, cast

IncidentCustomFieldSelectionResponseDataType = Literal["incident_custom_field_selections"]

INCIDENT_CUSTOM_FIELD_SELECTION_RESPONSE_DATA_TYPE_VALUES: set[IncidentCustomFieldSelectionResponseDataType] = {
    "incident_custom_field_selections",
}


def check_incident_custom_field_selection_response_data_type(
    value: str,
) -> IncidentCustomFieldSelectionResponseDataType:
    if value in INCIDENT_CUSTOM_FIELD_SELECTION_RESPONSE_DATA_TYPE_VALUES:
        return cast(IncidentCustomFieldSelectionResponseDataType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {INCIDENT_CUSTOM_FIELD_SELECTION_RESPONSE_DATA_TYPE_VALUES!r}"
    )
