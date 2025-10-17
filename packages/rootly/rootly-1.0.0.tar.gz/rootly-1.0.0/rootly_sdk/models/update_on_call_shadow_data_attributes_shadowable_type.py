from enum import Enum


class UpdateOnCallShadowDataAttributesShadowableType(str, Enum):
    SCHEDULE = "Schedule"
    USER = "User"

    def __str__(self) -> str:
        return str(self.value)
