from enum import Enum


class ArchiveSlackChannelsTaskParamsTaskType(str, Enum):
    ARCHIVE_SLACK_CHANNELS = "archive_slack_channels"

    def __str__(self) -> str:
        return str(self.value)
