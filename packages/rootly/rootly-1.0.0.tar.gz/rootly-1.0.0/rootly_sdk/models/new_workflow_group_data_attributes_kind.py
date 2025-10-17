from enum import Enum


class NewWorkflowGroupDataAttributesKind(str, Enum):
    ACTION_ITEM = "action_item"
    ALERT = "alert"
    INCIDENT = "incident"
    POST_MORTEM = "post_mortem"
    PULSE = "pulse"
    SIMPLE = "simple"

    def __str__(self) -> str:
        return str(self.value)
