from enum import Enum


class AlertRoutingRuleListDataItemType(str, Enum):
    ALERT_ROUTING_RULES = "alert_routing_rules"

    def __str__(self) -> str:
        return str(self.value)
