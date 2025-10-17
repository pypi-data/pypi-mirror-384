from enum import Enum


class WebhooksDeliveryResponseDataType(str, Enum):
    WEBHOOKS_DELIVERIES = "webhooks_deliveries"

    def __str__(self) -> str:
        return str(self.value)
