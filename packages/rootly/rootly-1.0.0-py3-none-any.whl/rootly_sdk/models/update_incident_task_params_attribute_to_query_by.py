from enum import Enum


class UpdateIncidentTaskParamsAttributeToQueryBy(str, Enum):
    AIRTABLE_RECORD_ID = "airtable_record_id"
    ASANA_TASK_ID = "asana_task_id"
    CLICKUP_TASK_ID = "clickup_task_id"
    FRESHSERVICE_TASK_ID = "freshservice_task_id"
    FRESHSERVICE_TICKET_ID = "freshservice_ticket_id"
    GITHUB_ISSUE_ID = "github_issue_id"
    GITLAB_ISSUE_ID = "gitlab_issue_id"
    ID = "id"
    JIRA_ISSUE_ID = "jira_issue_id"
    LINEAR_ISSUE_ID = "linear_issue_id"
    MOTION_TASK_ID = "motion_task_id"
    OPSGENIE_INCIDENT_ID = "opsgenie_incident_id"
    PAGERDUTY_INCIDENT_ID = "pagerduty_incident_id"
    SEQUENTIAL_ID = "sequential_id"
    SHORTCUT_STORY_ID = "shortcut_story_id"
    SHORTCUT_TASK_ID = "shortcut_task_id"
    SLUG = "slug"
    TRELLO_CARD_ID = "trello_card_id"
    VICTOR_OPS_INCIDENT_ID = "victor_ops_incident_id"
    ZENDESK_TICKET_ID = "zendesk_ticket_id"

    def __str__(self) -> str:
        return str(self.value)
