from enum import Enum


class CreateDropboxPaperPageTaskParamsTaskType(str, Enum):
    CREATE_DROPBOX_PAPER_PAGE = "create_dropbox_paper_page"

    def __str__(self) -> str:
        return str(self.value)
