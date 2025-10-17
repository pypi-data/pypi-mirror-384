from enum import Enum


class UpdateEscalationPolicyLevelDataAttributesPagingStrategyConfigurationStrategy(str, Enum):
    ALERT = "alert"
    CYCLE = "cycle"
    DEFAULT = "default"
    RANDOM = "random"

    def __str__(self) -> str:
        return str(self.value)
