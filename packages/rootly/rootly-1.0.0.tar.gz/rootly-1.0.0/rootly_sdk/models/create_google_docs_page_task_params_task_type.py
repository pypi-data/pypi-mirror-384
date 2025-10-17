from enum import Enum


class CreateGoogleDocsPageTaskParamsTaskType(str, Enum):
    CREATE_GOOGLE_DOCS_PAGE = "create_google_docs_page"

    def __str__(self) -> str:
        return str(self.value)
