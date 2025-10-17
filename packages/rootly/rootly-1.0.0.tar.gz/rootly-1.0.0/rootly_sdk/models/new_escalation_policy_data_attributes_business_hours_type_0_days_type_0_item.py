from enum import Enum


class NewEscalationPolicyDataAttributesBusinessHoursType0DaysType0Item(str, Enum):
    F = "F"
    M = "M"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    W = "W"

    def __str__(self) -> str:
        return str(self.value)
