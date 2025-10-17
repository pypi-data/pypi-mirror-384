from enum import Enum


class UpdateGoogleDocsPageTaskParamsTaskType(str, Enum):
    UPDATE_GOOGLE_DOCS_PAGE = "update_google_docs_page"

    def __str__(self) -> str:
        return str(self.value)
