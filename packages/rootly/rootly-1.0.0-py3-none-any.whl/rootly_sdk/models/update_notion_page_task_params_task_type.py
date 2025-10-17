from enum import Enum


class UpdateNotionPageTaskParamsTaskType(str, Enum):
    UPDATE_NOTION_PAGE = "update_notion_page"

    def __str__(self) -> str:
        return str(self.value)
