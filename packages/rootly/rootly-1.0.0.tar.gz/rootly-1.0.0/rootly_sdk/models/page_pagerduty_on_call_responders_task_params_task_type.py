from enum import Enum


class PagePagerdutyOnCallRespondersTaskParamsTaskType(str, Enum):
    PAGE_PAGERDUTY_ON_CALL_RESPONDERS = "page_pagerduty_on_call_responders"

    def __str__(self) -> str:
        return str(self.value)
