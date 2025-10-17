from enum import Enum


class RetrospectiveProcessGroupListDataItemType(str, Enum):
    RETROSPECTIVE_PROCESS_GROUPS = "retrospective_process_groups"

    def __str__(self) -> str:
        return str(self.value)
