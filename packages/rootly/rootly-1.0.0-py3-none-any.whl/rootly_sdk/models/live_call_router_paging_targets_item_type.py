from enum import Enum


class LiveCallRouterPagingTargetsItemType(str, Enum):
    ESCALATION_POLICY = "escalation_policy"
    SERVICE = "service"
    TEAM = "team"

    def __str__(self) -> str:
        return str(self.value)
