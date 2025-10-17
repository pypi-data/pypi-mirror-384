from enum import Enum


class NewAuthorizationDataAttributesPermissionsItem(str, Enum):
    AUTHORIZE = "authorize"
    DESTROY = "destroy"
    READ = "read"
    UPDATE = "update"

    def __str__(self) -> str:
        return str(self.value)
