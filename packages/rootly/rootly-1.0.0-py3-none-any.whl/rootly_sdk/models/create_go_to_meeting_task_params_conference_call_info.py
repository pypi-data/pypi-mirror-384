from enum import Enum


class CreateGoToMeetingTaskParamsConferenceCallInfo(str, Enum):
    FREE = "free"
    HYRID = "hyrid"
    PTSN = "ptsn"
    VOIP = "voip"

    def __str__(self) -> str:
        return str(self.value)
