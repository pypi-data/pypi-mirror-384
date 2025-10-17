from enum import Enum


class InviteToMicrosoftTeamsChannelTaskParamsTaskType(str, Enum):
    INVITE_TO_MICROSOFT_TEAMS_CHANNEL = "invite_to_microsoft_teams_channel"

    def __str__(self) -> str:
        return str(self.value)
