from enum import Enum


class NewSecretDataType(str, Enum):
    SECRETS = "secrets"

    def __str__(self) -> str:
        return str(self.value)
