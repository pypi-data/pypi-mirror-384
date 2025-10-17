from enum import Enum


class UpdateTrelloCardTaskParamsTaskType(str, Enum):
    UPDATE_TRELLO_CARD = "update_trello_card"

    def __str__(self) -> str:
        return str(self.value)
