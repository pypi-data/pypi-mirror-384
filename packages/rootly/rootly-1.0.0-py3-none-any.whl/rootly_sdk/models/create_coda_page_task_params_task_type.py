from enum import Enum


class CreateCodaPageTaskParamsTaskType(str, Enum):
    CREATE_CODA_PAGE = "create_coda_page"

    def __str__(self) -> str:
        return str(self.value)
