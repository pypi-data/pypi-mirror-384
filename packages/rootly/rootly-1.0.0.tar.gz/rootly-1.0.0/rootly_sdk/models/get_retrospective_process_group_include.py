from enum import Enum


class GetRetrospectiveProcessGroupInclude(str, Enum):
    RETROSPECTIVE_PROCESS_GROUP_STEPS = "retrospective_process_group_steps"

    def __str__(self) -> str:
        return str(self.value)
