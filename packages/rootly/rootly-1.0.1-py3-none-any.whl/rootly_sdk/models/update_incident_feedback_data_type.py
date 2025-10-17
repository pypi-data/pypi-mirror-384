from typing import Literal, cast

UpdateIncidentFeedbackDataType = Literal["incident_feedbacks"]

UPDATE_INCIDENT_FEEDBACK_DATA_TYPE_VALUES: set[UpdateIncidentFeedbackDataType] = {
    "incident_feedbacks",
}


def check_update_incident_feedback_data_type(value: str) -> UpdateIncidentFeedbackDataType:
    if value in UPDATE_INCIDENT_FEEDBACK_DATA_TYPE_VALUES:
        return cast(UpdateIncidentFeedbackDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_INCIDENT_FEEDBACK_DATA_TYPE_VALUES!r}")
