from enum import Enum


class SecretListDataItemType(str, Enum):
    SECRETS = "secrets"

    def __str__(self) -> str:
        return str(self.value)
