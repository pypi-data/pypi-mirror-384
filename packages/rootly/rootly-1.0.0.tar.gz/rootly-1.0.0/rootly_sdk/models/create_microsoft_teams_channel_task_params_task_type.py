from enum import Enum


class CreateMicrosoftTeamsChannelTaskParamsTaskType(str, Enum):
    CREATE_MICROSOFT_TEAMS_CHANNEL = "create_microsoft_teams_channel"

    def __str__(self) -> str:
        return str(self.value)
