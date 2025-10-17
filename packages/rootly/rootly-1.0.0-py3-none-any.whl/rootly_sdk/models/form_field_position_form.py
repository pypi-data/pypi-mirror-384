from enum import Enum


class FormFieldPositionForm(str, Enum):
    INCIDENT_POST_MORTEM = "incident_post_mortem"
    SLACK_INCIDENT_CANCELLATION_FORM = "slack_incident_cancellation_form"
    SLACK_INCIDENT_MITIGATION_FORM = "slack_incident_mitigation_form"
    SLACK_INCIDENT_RESOLUTION_FORM = "slack_incident_resolution_form"
    SLACK_NEW_INCIDENT_FORM = "slack_new_incident_form"
    SLACK_SCHEDULED_INCIDENT_FORM = "slack_scheduled_incident_form"
    SLACK_UPDATE_INCIDENT_FORM = "slack_update_incident_form"
    SLACK_UPDATE_INCIDENT_STATUS_FORM = "slack_update_incident_status_form"
    SLACK_UPDATE_SCHEDULED_INCIDENT_FORM = "slack_update_scheduled_incident_form"
    WEB_INCIDENT_CANCELLATION_FORM = "web_incident_cancellation_form"
    WEB_INCIDENT_MITIGATION_FORM = "web_incident_mitigation_form"
    WEB_INCIDENT_POST_MORTEM_FORM = "web_incident_post_mortem_form"
    WEB_INCIDENT_RESOLUTION_FORM = "web_incident_resolution_form"
    WEB_NEW_INCIDENT_FORM = "web_new_incident_form"
    WEB_SCHEDULED_INCIDENT_FORM = "web_scheduled_incident_form"
    WEB_UPDATE_INCIDENT_FORM = "web_update_incident_form"
    WEB_UPDATE_SCHEDULED_INCIDENT_FORM = "web_update_scheduled_incident_form"

    def __str__(self) -> str:
        return str(self.value)
