from enum import Enum


class NewEnvironmentDataType(str, Enum):
    ENVIRONMENTS = "environments"

    def __str__(self) -> str:
        return str(self.value)
