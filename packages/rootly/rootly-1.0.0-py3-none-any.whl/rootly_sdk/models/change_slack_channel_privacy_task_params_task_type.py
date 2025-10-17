from enum import Enum


class ChangeSlackChannelPrivacyTaskParamsTaskType(str, Enum):
    RENAME_SLACK_CHANNEL = "rename_slack_channel"

    def __str__(self) -> str:
        return str(self.value)
