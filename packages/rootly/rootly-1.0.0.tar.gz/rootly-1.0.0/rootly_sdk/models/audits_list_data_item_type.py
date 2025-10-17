from enum import Enum


class AuditsListDataItemType(str, Enum):
    AUDITS = "audits"

    def __str__(self) -> str:
        return str(self.value)
