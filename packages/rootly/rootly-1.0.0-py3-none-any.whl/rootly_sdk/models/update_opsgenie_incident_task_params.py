from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_opsgenie_incident_task_params_priority import UpdateOpsgenieIncidentTaskParamsPriority
from ..models.update_opsgenie_incident_task_params_status import UpdateOpsgenieIncidentTaskParamsStatus
from ..models.update_opsgenie_incident_task_params_task_type import UpdateOpsgenieIncidentTaskParamsTaskType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateOpsgenieIncidentTaskParams")


@_attrs_define
class UpdateOpsgenieIncidentTaskParams:
    """
    Attributes:
        opsgenie_incident_id (str): The Opsgenie incident ID, this can also be a Rootly incident variable ex. {{
            incident.opsgenie_incident_id }}
        task_type (Union[Unset, UpdateOpsgenieIncidentTaskParamsTaskType]):
        message (Union[Unset, str]): Message of the alert
        description (Union[Unset, str]): Description field of the alert that is generally used to provide a detailed
            information about the alert
        status (Union[Unset, UpdateOpsgenieIncidentTaskParamsStatus]):
        priority (Union[Unset, UpdateOpsgenieIncidentTaskParamsPriority]):
    """

    opsgenie_incident_id: str
    task_type: Union[Unset, UpdateOpsgenieIncidentTaskParamsTaskType] = UNSET
    message: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    status: Union[Unset, UpdateOpsgenieIncidentTaskParamsStatus] = UNSET
    priority: Union[Unset, UpdateOpsgenieIncidentTaskParamsPriority] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        opsgenie_incident_id = self.opsgenie_incident_id

        task_type: Union[Unset, str] = UNSET
        if not isinstance(self.task_type, Unset):
            task_type = self.task_type.value

        message = self.message

        description = self.description

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        priority: Union[Unset, str] = UNSET
        if not isinstance(self.priority, Unset):
            priority = self.priority.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "opsgenie_incident_id": opsgenie_incident_id,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type
        if message is not UNSET:
            field_dict["message"] = message
        if description is not UNSET:
            field_dict["description"] = description
        if status is not UNSET:
            field_dict["status"] = status
        if priority is not UNSET:
            field_dict["priority"] = priority

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        opsgenie_incident_id = d.pop("opsgenie_incident_id")

        _task_type = d.pop("task_type", UNSET)
        task_type: Union[Unset, UpdateOpsgenieIncidentTaskParamsTaskType]
        if isinstance(_task_type, Unset):
            task_type = UNSET
        else:
            task_type = UpdateOpsgenieIncidentTaskParamsTaskType(_task_type)

        message = d.pop("message", UNSET)

        description = d.pop("description", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, UpdateOpsgenieIncidentTaskParamsStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateOpsgenieIncidentTaskParamsStatus(_status)

        _priority = d.pop("priority", UNSET)
        priority: Union[Unset, UpdateOpsgenieIncidentTaskParamsPriority]
        if isinstance(_priority, Unset):
            priority = UNSET
        else:
            priority = UpdateOpsgenieIncidentTaskParamsPriority(_priority)

        update_opsgenie_incident_task_params = cls(
            opsgenie_incident_id=opsgenie_incident_id,
            task_type=task_type,
            message=message,
            description=description,
            status=status,
            priority=priority,
        )

        update_opsgenie_incident_task_params.additional_properties = d
        return update_opsgenie_incident_task_params

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
