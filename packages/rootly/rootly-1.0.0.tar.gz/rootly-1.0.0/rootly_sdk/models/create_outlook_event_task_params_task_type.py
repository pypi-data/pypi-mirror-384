from enum import Enum


class CreateOutlookEventTaskParamsTaskType(str, Enum):
    CREATE_OUTLOOK_EVENT = "create_outlook_event"

    def __str__(self) -> str:
        return str(self.value)
