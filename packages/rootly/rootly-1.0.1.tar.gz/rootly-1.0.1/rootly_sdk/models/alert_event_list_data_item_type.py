from typing import Literal, cast

AlertEventListDataItemType = Literal["alert_events"]

ALERT_EVENT_LIST_DATA_ITEM_TYPE_VALUES: set[AlertEventListDataItemType] = {
    "alert_events",
}


def check_alert_event_list_data_item_type(value: str) -> AlertEventListDataItemType:
    if value in ALERT_EVENT_LIST_DATA_ITEM_TYPE_VALUES:
        return cast(AlertEventListDataItemType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ALERT_EVENT_LIST_DATA_ITEM_TYPE_VALUES!r}")
