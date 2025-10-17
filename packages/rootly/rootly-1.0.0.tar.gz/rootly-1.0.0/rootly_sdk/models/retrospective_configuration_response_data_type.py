from enum import Enum


class RetrospectiveConfigurationResponseDataType(str, Enum):
    RETROSPECTIVE_CONFIGURATIONS = "retrospective_configurations"

    def __str__(self) -> str:
        return str(self.value)
