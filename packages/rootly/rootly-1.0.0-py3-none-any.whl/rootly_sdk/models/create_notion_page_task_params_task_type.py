from enum import Enum


class CreateNotionPageTaskParamsTaskType(str, Enum):
    CREATE_NOTION_PAGE = "create_notion_page"

    def __str__(self) -> str:
        return str(self.value)
