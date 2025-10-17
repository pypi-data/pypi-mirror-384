from enum import Enum


class PostMortemTriggerParamsIncidentPostMortemStatusesItem(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

    def __str__(self) -> str:
        return str(self.value)
