from enum import Enum


class UpdateAuthorizationDataAttributesPermissionsItem(str, Enum):
    AUTHORIZE = "authorize"
    DESTROY = "destroy"
    READ = "read"
    UPDATE = "update"

    def __str__(self) -> str:
        return str(self.value)
