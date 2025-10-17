from enum import Enum


class CreateZoomMeetingTaskParamsAutoRecording(str, Enum):
    CLOUD = "cloud"
    LOCAL = "local"
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
