from enum import Enum


class NewLiveCallRouterDataAttributesEscalationPolicyTriggerParamsType(str, Enum):
    ESCALATION_POLICY = "escalation_policy"
    GROUP = "group"
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
