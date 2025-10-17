from enum import Enum


class ServiceListDataItemType(str, Enum):
    SERVICES = "services"

    def __str__(self) -> str:
        return str(self.value)
