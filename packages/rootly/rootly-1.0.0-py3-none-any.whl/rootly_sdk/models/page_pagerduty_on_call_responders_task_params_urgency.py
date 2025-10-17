from enum import Enum


class PagePagerdutyOnCallRespondersTaskParamsUrgency(str, Enum):
    AUTO = "auto"
    HIGH = "high"
    LOW = "low"

    def __str__(self) -> str:
        return str(self.value)
