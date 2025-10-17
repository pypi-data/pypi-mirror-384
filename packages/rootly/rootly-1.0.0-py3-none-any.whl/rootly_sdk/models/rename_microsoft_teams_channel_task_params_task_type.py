from enum import Enum


class RenameMicrosoftTeamsChannelTaskParamsTaskType(str, Enum):
    RENAME_MICROSOFT_TEAMS_CHANNEL = "rename_microsoft_teams_channel"

    def __str__(self) -> str:
        return str(self.value)
