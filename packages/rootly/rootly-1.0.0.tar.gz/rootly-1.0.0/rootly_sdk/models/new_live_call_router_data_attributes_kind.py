from enum import Enum


class NewLiveCallRouterDataAttributesKind(str, Enum):
    LIVE = "live"
    VOICEMAIL = "voicemail"

    def __str__(self) -> str:
        return str(self.value)
