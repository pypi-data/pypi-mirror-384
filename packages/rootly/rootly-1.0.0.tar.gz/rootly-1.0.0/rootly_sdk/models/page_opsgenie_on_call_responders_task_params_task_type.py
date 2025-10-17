from enum import Enum


class PageOpsgenieOnCallRespondersTaskParamsTaskType(str, Enum):
    PAGE_OPSGENIE_ON_CALL_RESPONDERS = "page_opsgenie_on_call_responders"

    def __str__(self) -> str:
        return str(self.value)
