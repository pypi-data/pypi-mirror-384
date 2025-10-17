from enum import Enum


class CustomFieldShownItem(str, Enum):
    INCIDENT_FORM = "incident_form"
    INCIDENT_MITIGATION_FORM = "incident_mitigation_form"
    INCIDENT_MITIGATION_SLACK_FORM = "incident_mitigation_slack_form"
    INCIDENT_POST_MORTEM = "incident_post_mortem"
    INCIDENT_POST_MORTEM_FORM = "incident_post_mortem_form"
    INCIDENT_RESOLUTION_FORM = "incident_resolution_form"
    INCIDENT_RESOLUTION_SLACK_FORM = "incident_resolution_slack_form"
    INCIDENT_SLACK_FORM = "incident_slack_form"

    def __str__(self) -> str:
        return str(self.value)
