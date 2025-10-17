from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AlertsSourceAlertSourceFieldsAttributesType0Item")


@_attrs_define
class AlertsSourceAlertSourceFieldsAttributesType0Item:
    """
    Attributes:
        alert_field_id (Union[Unset, str]): The ID of the alert field
        template_body (Union[None, Unset, str]): Liquid expression to extract a specific value from the alert's payload
            for evaluation
    """

    alert_field_id: Union[Unset, str] = UNSET
    template_body: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        alert_field_id = self.alert_field_id

        template_body: Union[None, Unset, str]
        if isinstance(self.template_body, Unset):
            template_body = UNSET
        else:
            template_body = self.template_body

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if alert_field_id is not UNSET:
            field_dict["alert_field_id"] = alert_field_id
        if template_body is not UNSET:
            field_dict["template_body"] = template_body

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        alert_field_id = d.pop("alert_field_id", UNSET)

        def _parse_template_body(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        template_body = _parse_template_body(d.pop("template_body", UNSET))

        alerts_source_alert_source_fields_attributes_type_0_item = cls(
            alert_field_id=alert_field_id,
            template_body=template_body,
        )

        alerts_source_alert_source_fields_attributes_type_0_item.additional_properties = d
        return alerts_source_alert_source_fields_attributes_type_0_item

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
