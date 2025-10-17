from enum import Enum


class GetIncidentSubStatusInclude(str, Enum):
    ASSIGNED_BY_USER = "assigned_by_user"
    SUB_STATUS = "sub_status"

    def __str__(self) -> str:
        return str(self.value)
