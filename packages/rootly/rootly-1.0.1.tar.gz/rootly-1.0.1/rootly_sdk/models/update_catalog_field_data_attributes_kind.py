from typing import Literal, cast

UpdateCatalogFieldDataAttributesKind = Literal["reference", "text"]

UPDATE_CATALOG_FIELD_DATA_ATTRIBUTES_KIND_VALUES: set[UpdateCatalogFieldDataAttributesKind] = {
    "reference",
    "text",
}


def check_update_catalog_field_data_attributes_kind(value: str) -> UpdateCatalogFieldDataAttributesKind:
    if value in UPDATE_CATALOG_FIELD_DATA_ATTRIBUTES_KIND_VALUES:
        return cast(UpdateCatalogFieldDataAttributesKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_CATALOG_FIELD_DATA_ATTRIBUTES_KIND_VALUES!r}")
