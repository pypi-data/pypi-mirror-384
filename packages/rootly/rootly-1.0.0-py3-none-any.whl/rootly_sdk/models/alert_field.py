from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AlertField")


@_attrs_define
class AlertField:
    """
    Attributes:
        slug (str): The slug of the alert field
        name (str): The name of the alert field
        kind (str): The kind of alert field
        created_at (str): Date of creation
        updated_at (str): Date of last update
    """

    slug: str
    name: str
    kind: str
    created_at: str
    updated_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        slug = self.slug

        name = self.name

        kind = self.kind

        created_at = self.created_at

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "slug": slug,
                "name": name,
                "kind": kind,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        slug = d.pop("slug")

        name = d.pop("name")

        kind = d.pop("kind")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        alert_field = cls(
            slug=slug,
            name=name,
            kind=kind,
            created_at=created_at,
            updated_at=updated_at,
        )

        alert_field.additional_properties = d
        return alert_field

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
