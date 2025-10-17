from enum import Enum


class CreateWebexMeetingTaskParamsTaskType(str, Enum):
    CREATE_WEBEX_MEETING = "create_webex_meeting"

    def __str__(self) -> str:
        return str(self.value)
