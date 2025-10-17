from enum import Enum


class IpRangesResponseDataType(str, Enum):
    IP_RANGES = "ip_ranges"

    def __str__(self) -> str:
        return str(self.value)
