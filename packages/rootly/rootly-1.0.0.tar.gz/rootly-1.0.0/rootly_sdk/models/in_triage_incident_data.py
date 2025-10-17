from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.in_triage_incident_data_type import InTriageIncidentDataType

T = TypeVar("T", bound="InTriageIncidentData")


@_attrs_define
class InTriageIncidentData:
    """
    Attributes:
        type_ (InTriageIncidentDataType):
    """

    type_: InTriageIncidentDataType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        type_ = InTriageIncidentDataType(d.pop("type"))

        in_triage_incident_data = cls(
            type_=type_,
        )

        in_triage_incident_data.additional_properties = d
        return in_triage_incident_data

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
