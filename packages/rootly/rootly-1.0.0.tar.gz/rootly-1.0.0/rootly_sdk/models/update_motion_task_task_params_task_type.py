from enum import Enum


class UpdateMotionTaskTaskParamsTaskType(str, Enum):
    UPDATE_MOTION_TASK = "update_motion_task"

    def __str__(self) -> str:
        return str(self.value)
