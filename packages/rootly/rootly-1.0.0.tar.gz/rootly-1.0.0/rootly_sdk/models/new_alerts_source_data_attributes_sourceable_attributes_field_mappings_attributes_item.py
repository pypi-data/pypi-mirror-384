from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.new_alerts_source_data_attributes_sourceable_attributes_field_mappings_attributes_item_field import (
    NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItemField,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItem")


@_attrs_define
class NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItem:
    """
    Attributes:
        field (Union[Unset, NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItemField]): Select
            the field on which the condition to be evaluated
        json_path (Union[Unset, str]): JSON path expression to extract a specific value from the alert's payload for
            evaluation
    """

    field: Union[Unset, NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItemField] = UNSET
    json_path: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field: Union[Unset, str] = UNSET
        if not isinstance(self.field, Unset):
            field = self.field.value

        json_path = self.json_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if field is not UNSET:
            field_dict["field"] = field
        if json_path is not UNSET:
            field_dict["json_path"] = json_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        _field = d.pop("field", UNSET)
        field: Union[Unset, NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItemField]
        if isinstance(_field, Unset):
            field = UNSET
        else:
            field = NewAlertsSourceDataAttributesSourceableAttributesFieldMappingsAttributesItemField(_field)

        json_path = d.pop("json_path", UNSET)

        new_alerts_source_data_attributes_sourceable_attributes_field_mappings_attributes_item = cls(
            field=field,
            json_path=json_path,
        )

        new_alerts_source_data_attributes_sourceable_attributes_field_mappings_attributes_item.additional_properties = d
        return new_alerts_source_data_attributes_sourceable_attributes_field_mappings_attributes_item

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
