from enum import Enum


class IncidentPermissionSetBooleanKind(str, Enum):
    ASSIGN_INCIDENT_ROLES = "assign_incident_roles"
    CREATE_COMMUNICATIONS = "create_communications"
    DELETE_COMMUNICATIONS = "delete_communications"
    INVITE_SUBSCRIBERS = "invite_subscribers"
    MODIFY_CUSTOM_FIELDS = "modify_custom_fields"
    PUBLISH_TO_STATUS_PAGE = "publish_to_status_page"
    READ_COMMUNICATIONS = "read_communications"
    SEND_COMMUNICATIONS = "send_communications"
    TRIGGER_WORKFLOWS = "trigger_workflows"
    UPDATE_COMMUNICATIONS = "update_communications"
    UPDATE_SUMMARY = "update_summary"
    UPDATE_TIMELINE = "update_timeline"

    def __str__(self) -> str:
        return str(self.value)
