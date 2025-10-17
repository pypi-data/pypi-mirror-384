from enum import Enum


class WebhooksDeliveryListDataItemType(str, Enum):
    WEBHOOKS_DELIVERIES = "webhooks_deliveries"

    def __str__(self) -> str:
        return str(self.value)
