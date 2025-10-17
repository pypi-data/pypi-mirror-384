from typing import Literal, cast

NewCatalogFieldDataAttributesKind = Literal["reference", "text"]

NEW_CATALOG_FIELD_DATA_ATTRIBUTES_KIND_VALUES: set[NewCatalogFieldDataAttributesKind] = {
    "reference",
    "text",
}


def check_new_catalog_field_data_attributes_kind(value: str) -> NewCatalogFieldDataAttributesKind:
    if value in NEW_CATALOG_FIELD_DATA_ATTRIBUTES_KIND_VALUES:
        return cast(NewCatalogFieldDataAttributesKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {NEW_CATALOG_FIELD_DATA_ATTRIBUTES_KIND_VALUES!r}")
