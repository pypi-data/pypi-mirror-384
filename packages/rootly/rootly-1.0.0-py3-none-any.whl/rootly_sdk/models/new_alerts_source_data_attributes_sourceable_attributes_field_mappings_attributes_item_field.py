from enum import Enum


class NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItemField(str, Enum):
    ALERT_EXTERNAL_URL = "alert_external_url"
    ALERT_TITLE = "alert_title"
    EXTERNAL_ID = "external_id"
    NOTIFICATION_TARGET_ID = "notification_target_id"
    NOTIFICATION_TARGET_TYPE = "notification_target_type"
    STATE = "state"

    def __str__(self) -> str:
        return str(self.value)
