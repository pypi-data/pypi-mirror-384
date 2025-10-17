from typing import Literal, cast

SeverityListDataItemType = Literal["severities"]

SEVERITY_LIST_DATA_ITEM_TYPE_VALUES: set[SeverityListDataItemType] = {
    "severities",
}


def check_severity_list_data_item_type(value: str) -> SeverityListDataItemType:
    if value in SEVERITY_LIST_DATA_ITEM_TYPE_VALUES:
        return cast(SeverityListDataItemType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {SEVERITY_LIST_DATA_ITEM_TYPE_VALUES!r}")
