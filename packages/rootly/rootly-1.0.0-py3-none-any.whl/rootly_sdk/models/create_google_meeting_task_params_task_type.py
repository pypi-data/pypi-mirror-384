from enum import Enum


class CreateGoogleMeetingTaskParamsTaskType(str, Enum):
    CREATE_GOOGLE_MEETING = "create_google_meeting"

    def __str__(self) -> str:
        return str(self.value)
