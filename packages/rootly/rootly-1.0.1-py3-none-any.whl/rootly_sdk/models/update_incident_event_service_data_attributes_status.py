from typing import Literal, cast

UpdateIncidentEventServiceDataAttributesStatus = Literal["major_outage", "operational", "partial_outage"]

UPDATE_INCIDENT_EVENT_SERVICE_DATA_ATTRIBUTES_STATUS_VALUES: set[UpdateIncidentEventServiceDataAttributesStatus] = {
    "major_outage",
    "operational",
    "partial_outage",
}


def check_update_incident_event_service_data_attributes_status(
    value: str,
) -> UpdateIncidentEventServiceDataAttributesStatus:
    if value in UPDATE_INCIDENT_EVENT_SERVICE_DATA_ATTRIBUTES_STATUS_VALUES:
        return cast(UpdateIncidentEventServiceDataAttributesStatus, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_INCIDENT_EVENT_SERVICE_DATA_ATTRIBUTES_STATUS_VALUES!r}"
    )
