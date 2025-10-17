from enum import Enum


class CreateGoToMeetingTaskParamsTaskType(str, Enum):
    CREATE_GO_TO_MEETING_TASK = "create_go_to_meeting_task"

    def __str__(self) -> str:
        return str(self.value)
