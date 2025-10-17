from typing import Literal, cast

CatalogListDataItemType = Literal["catalogs"]

CATALOG_LIST_DATA_ITEM_TYPE_VALUES: set[CatalogListDataItemType] = {
    "catalogs",
}


def check_catalog_list_data_item_type(value: str) -> CatalogListDataItemType:
    if value in CATALOG_LIST_DATA_ITEM_TYPE_VALUES:
        return cast(CatalogListDataItemType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {CATALOG_LIST_DATA_ITEM_TYPE_VALUES!r}")
