from enum import Enum


class UpdateRetrospectiveStepDataType(str, Enum):
    RETROSPECTIVE_STEPS = "retrospective_steps"

    def __str__(self) -> str:
        return str(self.value)
