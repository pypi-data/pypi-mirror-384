from enum import Enum


class UpdatePagerdutyIncidentTaskParamsTaskType(str, Enum):
    UPDATE_PAGERDUTY_INCIDENT = "update_pagerduty_incident"

    def __str__(self) -> str:
        return str(self.value)
