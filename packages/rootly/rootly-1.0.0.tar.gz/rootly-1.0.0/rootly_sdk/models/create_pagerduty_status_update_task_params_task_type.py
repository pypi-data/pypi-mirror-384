from enum import Enum


class CreatePagerdutyStatusUpdateTaskParamsTaskType(str, Enum):
    CREATE_PAGERDUTY_STATUS_UPDATE = "create_pagerduty_status_update"

    def __str__(self) -> str:
        return str(self.value)
