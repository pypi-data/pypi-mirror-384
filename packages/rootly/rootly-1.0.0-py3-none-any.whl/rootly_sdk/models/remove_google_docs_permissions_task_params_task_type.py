from enum import Enum


class RemoveGoogleDocsPermissionsTaskParamsTaskType(str, Enum):
    REMOVE_GOOGLE_DOCS_PERMISSIONS = "remove_google_docs_permissions"

    def __str__(self) -> str:
        return str(self.value)
