from enum import Enum


class UpdateCodaPageTaskParamsTaskType(str, Enum):
    UPDATE_CODA_PAGE = "update_coda_page"

    def __str__(self) -> str:
        return str(self.value)
