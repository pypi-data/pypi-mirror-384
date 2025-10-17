from enum import Enum


class RetrospectiveStepResponseDataType(str, Enum):
    RETROSPECTIVE_STEPS = "retrospective_steps"

    def __str__(self) -> str:
        return str(self.value)
