from enum import Enum


class UpdateVictorOpsIncidentTaskParamsStatus(str, Enum):
    ACK = "ack"
    AUTO = "auto"
    RESOLVE = "resolve"

    def __str__(self) -> str:
        return str(self.value)
