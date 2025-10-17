from enum import Enum


class GetIncidentInclude(str, Enum):
    ACTION_ITEMS = "action_items"
    CAUSES = "causes"
    CUSTOM_FIELD_SELECTIONS = "custom_field_selections"
    ENVIRONMENTS = "environments"
    EVENTS = "events"
    FEEDBACKS = "feedbacks"
    FUNCTIONALITIES = "functionalities"
    GROUPS = "groups"
    INCIDENT_POST_MORTEM = "incident_post_mortem"
    INCIDENT_TYPES = "incident_types"
    ROLES = "roles"
    SERVICES = "services"
    SLACK_MESSAGES = "slack_messages"
    SUBSCRIBERS = "subscribers"
    SUB_STATUSES = "sub_statuses"

    def __str__(self) -> str:
        return str(self.value)
