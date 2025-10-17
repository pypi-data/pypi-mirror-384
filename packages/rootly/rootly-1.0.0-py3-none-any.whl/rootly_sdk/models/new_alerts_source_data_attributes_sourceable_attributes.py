from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.new_alerts_source_data_attributes_sourceable_attributes_field_mappings_attributes_item import (
        NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItem,
    )


T = TypeVar("T", bound="NewAlertsSourceDataAttributesSourceableAttributes")


@_attrs_define
class NewAlertsSourceDataAttributesSourceableAttributes:
    """Provide additional attributes for generic_webhook alerts source

    Attributes:
        auto_resolve (Union[Unset, bool]): Set this to true to auto-resolve alerts based on field_mappings_attributes
            conditions
        resolve_state (Union[Unset, str]): This value is matched with the value extracted from alerts payload using JSON
            path in field_mappings_attributes
        accept_threaded_emails (Union[Unset, bool]): Set this to false to reject threaded emails
        field_mappings_attributes (Union[Unset,
            list['NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItem']]): Specify rules to auto
            resolve alerts
    """

    auto_resolve: Union[Unset, bool] = UNSET
    resolve_state: Union[Unset, str] = UNSET
    accept_threaded_emails: Union[Unset, bool] = UNSET
    field_mappings_attributes: Union[
        Unset, list["NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItem"]
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_resolve = self.auto_resolve

        resolve_state = self.resolve_state

        accept_threaded_emails = self.accept_threaded_emails

        field_mappings_attributes: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.field_mappings_attributes, Unset):
            field_mappings_attributes = []
            for field_mappings_attributes_item_data in self.field_mappings_attributes:
                field_mappings_attributes_item = field_mappings_attributes_item_data.to_dict()
                field_mappings_attributes.append(field_mappings_attributes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if auto_resolve is not UNSET:
            field_dict["auto_resolve"] = auto_resolve
        if resolve_state is not UNSET:
            field_dict["resolve_state"] = resolve_state
        if accept_threaded_emails is not UNSET:
            field_dict["accept_threaded_emails"] = accept_threaded_emails
        if field_mappings_attributes is not UNSET:
            field_dict["field_mappings_attributes"] = field_mappings_attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.new_alerts_source_data_attributes_sourceable_attributes_field_mappings_attributes_item import (
            NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItem,
        )

        d = src_dict.copy()
        auto_resolve = d.pop("auto_resolve", UNSET)

        resolve_state = d.pop("resolve_state", UNSET)

        accept_threaded_emails = d.pop("accept_threaded_emails", UNSET)

        field_mappings_attributes = []
        _field_mappings_attributes = d.pop("field_mappings_attributes", UNSET)
        for field_mappings_attributes_item_data in _field_mappings_attributes or []:
            field_mappings_attributes_item = (
                NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItem.from_dict(
                    field_mappings_attributes_item_data
                )
            )

            field_mappings_attributes.append(field_mappings_attributes_item)

        new_alerts_source_data_attributes_sourceable_attributes = cls(
            auto_resolve=auto_resolve,
            resolve_state=resolve_state,
            accept_threaded_emails=accept_threaded_emails,
            field_mappings_attributes=field_mappings_attributes,
        )

        new_alerts_source_data_attributes_sourceable_attributes.additional_properties = d
        return new_alerts_source_data_attributes_sourceable_attributes

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
