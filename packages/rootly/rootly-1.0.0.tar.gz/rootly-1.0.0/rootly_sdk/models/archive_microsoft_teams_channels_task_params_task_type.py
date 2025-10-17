from enum import Enum


class ArchiveMicrosoftTeamsChannelsTaskParamsTaskType(str, Enum):
    ARCHIVE_MICROSOFT_TEAMS_CHANNELS = "archive_microsoft_teams_channels"

    def __str__(self) -> str:
        return str(self.value)
