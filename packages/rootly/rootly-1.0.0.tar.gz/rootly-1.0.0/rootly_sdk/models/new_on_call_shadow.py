from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.new_on_call_shadow_data import NewOnCallShadowData


T = TypeVar("T", bound="NewOnCallShadow")


@_attrs_define
class NewOnCallShadow:
    """
    Attributes:
        data (NewOnCallShadowData):
    """

    data: "NewOnCallShadowData"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.new_on_call_shadow_data import NewOnCallShadowData

        d = src_dict.copy()
        data = NewOnCallShadowData.from_dict(d.pop("data"))

        new_on_call_shadow = cls(
            data=data,
        )

        new_on_call_shadow.additional_properties = d
        return new_on_call_shadow

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
