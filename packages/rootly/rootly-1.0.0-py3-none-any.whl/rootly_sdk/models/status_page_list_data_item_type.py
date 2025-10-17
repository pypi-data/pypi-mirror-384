from enum import Enum


class StatusPageListDataItemType(str, Enum):
    STATUS_PAGES = "status_pages"

    def __str__(self) -> str:
        return str(self.value)
