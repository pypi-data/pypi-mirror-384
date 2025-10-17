from enum import Enum


class UpdateOnCallShadowDataType(str, Enum):
    ON_CALL_SHADOWS = "on_call_shadows"

    def __str__(self) -> str:
        return str(self.value)
