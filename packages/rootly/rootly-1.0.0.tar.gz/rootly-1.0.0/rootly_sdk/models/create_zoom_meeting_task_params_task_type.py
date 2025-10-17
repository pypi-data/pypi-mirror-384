from enum import Enum


class CreateZoomMeetingTaskParamsTaskType(str, Enum):
    CREATE_ZOOM_MEETING = "create_zoom_meeting"

    def __str__(self) -> str:
        return str(self.value)
