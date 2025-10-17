from enum import Enum


class EscalationPolicyPathRulesItemType2RuleType(str, Enum):
    JSON_PATH = "json_path"

    def __str__(self) -> str:
        return str(self.value)
