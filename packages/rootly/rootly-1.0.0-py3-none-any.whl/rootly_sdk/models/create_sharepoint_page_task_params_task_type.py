from enum import Enum


class CreateSharepointPageTaskParamsTaskType(str, Enum):
    CREATE_SHAREPOINT_PAGE = "create_sharepoint_page"

    def __str__(self) -> str:
        return str(self.value)
