from enum import Enum


class OnCallShadowShadowableType(str, Enum):
    SCHEDULE = "Schedule"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
