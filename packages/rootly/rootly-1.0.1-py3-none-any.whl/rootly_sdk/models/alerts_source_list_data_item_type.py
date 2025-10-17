from typing import Literal, cast

AlertsSourceListDataItemType = Literal["alert_sources"]

ALERTS_SOURCE_LIST_DATA_ITEM_TYPE_VALUES: set[AlertsSourceListDataItemType] = {
    "alert_sources",
}


def check_alerts_source_list_data_item_type(value: str) -> AlertsSourceListDataItemType:
    if value in ALERTS_SOURCE_LIST_DATA_ITEM_TYPE_VALUES:
        return cast(AlertsSourceListDataItemType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ALERTS_SOURCE_LIST_DATA_ITEM_TYPE_VALUES!r}")
