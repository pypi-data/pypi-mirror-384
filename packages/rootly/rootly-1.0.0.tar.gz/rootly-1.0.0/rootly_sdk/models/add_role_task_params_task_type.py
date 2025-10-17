from enum import Enum


class AddRoleTaskParamsTaskType(str, Enum):
    ADD_ROLE = "add_role"

    def __str__(self) -> str:
        return str(self.value)
