from enum import Enum


class SeverityListDataItemType(str, Enum):
    SEVERITIES = "severities"

    def __str__(self) -> str:
        return str(self.value)
