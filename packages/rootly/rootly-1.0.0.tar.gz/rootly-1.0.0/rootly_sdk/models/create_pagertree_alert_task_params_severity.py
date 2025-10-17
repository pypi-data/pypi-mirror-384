from enum import Enum


class CreatePagertreeAlertTaskParamsSeverity(str, Enum):
    AUTO = "auto"
    SEV_1 = "SEV-1"
    SEV_2 = "SEV-2"
    SEV_3 = "SEV-3"
    SEV_4 = "SEV-4"

    def __str__(self) -> str:
        return str(self.value)
