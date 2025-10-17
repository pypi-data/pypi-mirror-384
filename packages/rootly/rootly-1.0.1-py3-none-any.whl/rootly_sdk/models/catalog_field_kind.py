from typing import Literal, cast

CatalogFieldKind = Literal["reference", "text"]

CATALOG_FIELD_KIND_VALUES: set[CatalogFieldKind] = {
    "reference",
    "text",
}


def check_catalog_field_kind(value: str) -> CatalogFieldKind:
    if value in CATALOG_FIELD_KIND_VALUES:
        return cast(CatalogFieldKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {CATALOG_FIELD_KIND_VALUES!r}")
