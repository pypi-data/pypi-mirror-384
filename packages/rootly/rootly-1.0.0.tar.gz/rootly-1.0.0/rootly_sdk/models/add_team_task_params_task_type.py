from enum import Enum


class AddTeamTaskParamsTaskType(str, Enum):
    ADD_TEAM = "add_team"

    def __str__(self) -> str:
        return str(self.value)
