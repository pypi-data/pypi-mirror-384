from enum import Enum


class CreateConfluencePageTaskParamsTaskType(str, Enum):
    CREATE_CONFLUENCE_PAGE = "create_confluence_page"

    def __str__(self) -> str:
        return str(self.value)
