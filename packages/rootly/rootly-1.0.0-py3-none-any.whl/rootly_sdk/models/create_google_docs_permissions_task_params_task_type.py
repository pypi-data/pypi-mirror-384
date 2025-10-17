from enum import Enum


class CreateGoogleDocsPermissionsTaskParamsTaskType(str, Enum):
    CREATE_GOOGLE_DOCS_PERMISSIONS = "create_google_docs_permissions"

    def __str__(self) -> str:
        return str(self.value)
