from enum import Enum


class CreateMotionTaskTaskParamsTaskType(str, Enum):
    CREATE_MOTION_TASK = "create_motion_task"

    def __str__(self) -> str:
        return str(self.value)
