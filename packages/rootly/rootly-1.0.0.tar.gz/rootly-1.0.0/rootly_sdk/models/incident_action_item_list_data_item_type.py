from enum import Enum


class IncidentActionItemListDataItemType(str, Enum):
    INCIDENT_ACTION_ITEMS = "incident_action_items"

    def __str__(self) -> str:
        return str(self.value)
