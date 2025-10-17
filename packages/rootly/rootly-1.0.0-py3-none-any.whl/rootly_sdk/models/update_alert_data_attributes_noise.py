from enum import Enum


class UpdateAlertDataAttributesNoise(str, Enum):
    NOISE = "noise"
    NOT_NOISE = "not_noise"

    def __str__(self) -> str:
        return str(self.value)
