from enum import Enum


class PostMortemTriggerParamsTriggerType(str, Enum):
    POST_MORTEM = "post_mortem"

    def __str__(self) -> str:
        return str(self.value)
