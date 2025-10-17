from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.live_call_router_list_data_item_type import LiveCallRouterListDataItemType

if TYPE_CHECKING:
    from ..models.live_call_router import LiveCallRouter


T = TypeVar("T", bound="LiveCallRouterListDataItem")


@_attrs_define
class LiveCallRouterListDataItem:
    """
    Attributes:
        id (str): Unique ID of the live_call_router
        type_ (LiveCallRouterListDataItemType):
        attributes (LiveCallRouter):
    """

    id: str
    type_: LiveCallRouterListDataItemType
    attributes: "LiveCallRouter"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_.value

        attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.live_call_router import LiveCallRouter

        d = src_dict.copy()
        id = d.pop("id")

        type_ = LiveCallRouterListDataItemType(d.pop("type"))

        attributes = LiveCallRouter.from_dict(d.pop("attributes"))

        live_call_router_list_data_item = cls(
            id=id,
            type_=type_,
            attributes=attributes,
        )

        live_call_router_list_data_item.additional_properties = d
        return live_call_router_list_data_item

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
