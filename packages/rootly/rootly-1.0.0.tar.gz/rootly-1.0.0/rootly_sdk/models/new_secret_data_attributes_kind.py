from enum import Enum


class NewSecretDataAttributesKind(str, Enum):
    BUILT_IN = "built_in"
    HASHICORP_VAULT = "hashicorp_vault"

    def __str__(self) -> str:
        return str(self.value)
