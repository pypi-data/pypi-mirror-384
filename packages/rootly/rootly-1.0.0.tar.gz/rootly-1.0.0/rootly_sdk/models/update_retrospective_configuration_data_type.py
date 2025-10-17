from enum import Enum


class UpdateRetrospectiveConfigurationDataType(str, Enum):
    RETROSPECTIVE_CONFIGURATIONS = "retrospective_configurations"

    def __str__(self) -> str:
        return str(self.value)
