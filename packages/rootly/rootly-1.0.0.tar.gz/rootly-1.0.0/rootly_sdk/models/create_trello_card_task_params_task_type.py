from enum import Enum


class CreateTrelloCardTaskParamsTaskType(str, Enum):
    CREATE_TRELLO_CARD = "create_trello_card"

    def __str__(self) -> str:
        return str(self.value)
