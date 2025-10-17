from enum import Enum


class IncidentPostMortemResponseDataType(str, Enum):
    INCIDENT_POST_MORTEMS = "incident_post_mortems"

    def __str__(self) -> str:
        return str(self.value)
