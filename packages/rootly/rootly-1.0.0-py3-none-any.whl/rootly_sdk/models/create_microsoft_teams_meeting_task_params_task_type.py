from enum import Enum


class CreateMicrosoftTeamsMeetingTaskParamsTaskType(str, Enum):
    CREATE_MICROSOFT_TEAMS_MEETING = "create_microsoft_teams_meeting"

    def __str__(self) -> str:
        return str(self.value)
