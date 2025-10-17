from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_incident_event_service_data_attributes_status import UpdateIncidentEventServiceDataAttributesStatus

T = TypeVar("T", bound="UpdateIncidentEventServiceDataAttributes")


@_attrs_define
class UpdateIncidentEventServiceDataAttributes:
    """
    Attributes:
        status (UpdateIncidentEventServiceDataAttributesStatus): The status of the affected service
    """

    status: UpdateIncidentEventServiceDataAttributesStatus

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        status = UpdateIncidentEventServiceDataAttributesStatus(d.pop("status"))

        update_incident_event_service_data_attributes = cls(
            status=status,
        )

        return update_incident_event_service_data_attributes
