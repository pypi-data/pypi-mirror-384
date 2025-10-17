from enum import Enum


class AddToTimelineTaskParamsTaskType(str, Enum):
    ADD_TO_TIMELINE = "add_to_timeline"

    def __str__(self) -> str:
        return str(self.value)
