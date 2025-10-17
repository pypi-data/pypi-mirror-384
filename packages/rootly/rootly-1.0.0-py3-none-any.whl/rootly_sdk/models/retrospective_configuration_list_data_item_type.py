from enum import Enum


class RetrospectiveConfigurationListDataItemType(str, Enum):
    RETROSPECTIVE_CONFIGURATIONS = "retrospective_configurations"

    def __str__(self) -> str:
        return str(self.value)
