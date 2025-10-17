from enum import Enum


class RemoveGoogleDocsPermissionsTaskParamsAttributeToQueryBy(str, Enum):
    EMAIL_ADDRESS = "email_address"
    ROLE = "role"
    TYPE = "type"

    def __str__(self) -> str:
        return str(self.value)
