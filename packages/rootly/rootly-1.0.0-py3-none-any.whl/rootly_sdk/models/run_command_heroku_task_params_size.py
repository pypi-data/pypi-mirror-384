from enum import Enum


class RunCommandHerokuTaskParamsSize(str, Enum):
    STANDARD_1X = "standard-1X"
    STANDARD_2X = "standard-2X"

    def __str__(self) -> str:
        return str(self.value)
