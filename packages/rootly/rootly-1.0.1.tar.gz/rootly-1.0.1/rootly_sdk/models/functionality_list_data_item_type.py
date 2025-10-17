from typing import Literal, cast

FunctionalityListDataItemType = Literal["functionalities"]

FUNCTIONALITY_LIST_DATA_ITEM_TYPE_VALUES: set[FunctionalityListDataItemType] = {
    "functionalities",
}


def check_functionality_list_data_item_type(value: str) -> FunctionalityListDataItemType:
    if value in FUNCTIONALITY_LIST_DATA_ITEM_TYPE_VALUES:
        return cast(FunctionalityListDataItemType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {FUNCTIONALITY_LIST_DATA_ITEM_TYPE_VALUES!r}")
