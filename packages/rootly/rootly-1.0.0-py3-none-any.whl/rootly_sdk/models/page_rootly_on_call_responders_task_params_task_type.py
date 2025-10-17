from enum import Enum


class PageRootlyOnCallRespondersTaskParamsTaskType(str, Enum):
    PAGE_ROOTLY_ON_CALL_RESPONDERS = "page_rootly_on_call_responders"

    def __str__(self) -> str:
        return str(self.value)
