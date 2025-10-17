from enum import Enum


class GetEscalationPolicyInclude(str, Enum):
    ESCALATION_POLICY_LEVELS = "escalation_policy_levels"
    ESCALATION_POLICY_PATHS = "escalation_policy_paths"
    GROUPS = "groups"
    SERVICES = "services"

    def __str__(self) -> str:
        return str(self.value)
