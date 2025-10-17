from enum import Enum


class CommunicationsStageResponseDataType(str, Enum):
    COMMUNICATIONS_STAGES = "communications_stages"

    def __str__(self) -> str:
        return str(self.value)
