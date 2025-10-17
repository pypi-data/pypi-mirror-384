from enum import Enum


class NewFormFieldDataAttributesKind(str, Enum):
    ACKNOWLEDGED_AT = "acknowledged_at"
    ATTACH_ALERTS = "attach_alerts"
    CAUSES = "causes"
    CLOSED_AT = "closed_at"
    CUSTOM = "custom"
    DETECTED_AT = "detected_at"
    ENVIRONMENTS = "environments"
    FUNCTIONALITIES = "functionalities"
    IN_TRIAGE_AT = "in_triage_at"
    LABELS = "labels"
    MANUAL_STARTING_DATETIME_FIELD = "manual_starting_datetime_field"
    MARK_AS_BACKFILLED = "mark_as_backfilled"
    MARK_AS_IN_TRIAGE = "mark_as_in_triage"
    MARK_AS_TEST = "mark_as_test"
    MITIGATED_AT = "mitigated_at"
    MITIGATION_MESSAGE = "mitigation_message"
    NOTIFY_EMAILS = "notify_emails"
    RESOLUTION_MESSAGE = "resolution_message"
    RESOLVED_AT = "resolved_at"
    SERVICES = "services"
    SEVERITY = "severity"
    SHOW_ONGOING_INCIDENTS = "show_ongoing_incidents"
    STARTED_AT = "started_at"
    SUMMARY = "summary"
    TEAMS = "teams"
    TITLE = "title"
    TRIGGER_MANUAL_WORKFLOWS = "trigger_manual_workflows"
    TYPES = "types"
    VISIBILITY = "visibility"

    def __str__(self) -> str:
        return str(self.value)
