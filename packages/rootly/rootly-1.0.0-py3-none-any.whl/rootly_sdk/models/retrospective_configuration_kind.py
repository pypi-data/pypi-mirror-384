from enum import Enum


class RetrospectiveConfigurationKind(str, Enum):
    MANDATORY = "mandatory"
    SKIP = "skip"

    def __str__(self) -> str:
        return str(self.value)
