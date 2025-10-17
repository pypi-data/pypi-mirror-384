from enum import Enum


class ChangeSlackChannelPrivacyTaskParamsPrivacy(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"

    def __str__(self) -> str:
        return str(self.value)
