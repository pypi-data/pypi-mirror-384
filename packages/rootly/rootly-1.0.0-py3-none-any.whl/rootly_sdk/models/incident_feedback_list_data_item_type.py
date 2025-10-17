from enum import Enum


class IncidentFeedbackListDataItemType(str, Enum):
    INCIDENT_FEEDBACKS = "incident_feedbacks"

    def __str__(self) -> str:
        return str(self.value)
