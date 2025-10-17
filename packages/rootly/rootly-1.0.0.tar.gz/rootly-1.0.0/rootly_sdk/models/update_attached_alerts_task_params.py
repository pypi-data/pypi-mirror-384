from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_attached_alerts_task_params_status import UpdateAttachedAlertsTaskParamsStatus
from ..models.update_attached_alerts_task_params_task_type import UpdateAttachedAlertsTaskParamsTaskType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAttachedAlertsTaskParams")


@_attrs_define
class UpdateAttachedAlertsTaskParams:
    """
    Attributes:
        status (UpdateAttachedAlertsTaskParamsStatus):
        task_type (Union[Unset, UpdateAttachedAlertsTaskParamsTaskType]):
    """

    status: UpdateAttachedAlertsTaskParamsStatus
    task_type: Union[Unset, UpdateAttachedAlertsTaskParamsTaskType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        task_type: Union[Unset, str] = UNSET
        if not isinstance(self.task_type, Unset):
            task_type = self.task_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        status = UpdateAttachedAlertsTaskParamsStatus(d.pop("status"))

        _task_type = d.pop("task_type", UNSET)
        task_type: Union[Unset, UpdateAttachedAlertsTaskParamsTaskType]
        if isinstance(_task_type, Unset):
            task_type = UNSET
        else:
            task_type = UpdateAttachedAlertsTaskParamsTaskType(_task_type)

        update_attached_alerts_task_params = cls(
            status=status,
            task_type=task_type,
        )

        update_attached_alerts_task_params.additional_properties = d
        return update_attached_alerts_task_params

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
