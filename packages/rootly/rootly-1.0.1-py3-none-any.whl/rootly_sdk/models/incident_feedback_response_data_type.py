from typing import Literal, cast

IncidentFeedbackResponseDataType = Literal["incident_feedbacks"]

INCIDENT_FEEDBACK_RESPONSE_DATA_TYPE_VALUES: set[IncidentFeedbackResponseDataType] = {
    "incident_feedbacks",
}


def check_incident_feedback_response_data_type(value: str) -> IncidentFeedbackResponseDataType:
    if value in INCIDENT_FEEDBACK_RESPONSE_DATA_TYPE_VALUES:
        return cast(IncidentFeedbackResponseDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {INCIDENT_FEEDBACK_RESPONSE_DATA_TYPE_VALUES!r}")
