from enum import Enum


class LiveCallRouterResponseDataType(str, Enum):
    LIVE_CALL_ROUTERS = "live_call_routers"

    def __str__(self) -> str:
        return str(self.value)
