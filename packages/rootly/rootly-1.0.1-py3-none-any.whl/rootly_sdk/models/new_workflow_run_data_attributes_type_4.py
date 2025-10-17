from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.new_workflow_run_data_attributes_type_4_context import NewWorkflowRunDataAttributesType4Context


T = TypeVar("T", bound="NewWorkflowRunDataAttributesType4")


@_attrs_define
class NewWorkflowRunDataAttributesType4:
    """
    Attributes:
        alert_id (str):
        immediate (Union[None, Unset, bool]): If false, this will respect wait time configured on the workflow Default:
            True.
        check_conditions (Union[None, Unset, bool]): If true, this will check conditions. If conditions are not
            satisfied the run will not be created Default: False.
        context (Union[Unset, NewWorkflowRunDataAttributesType4Context]):
    """

    alert_id: str
    immediate: Union[None, Unset, bool] = True
    check_conditions: Union[None, Unset, bool] = False
    context: Union[Unset, "NewWorkflowRunDataAttributesType4Context"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        alert_id = self.alert_id

        immediate: Union[None, Unset, bool]
        if isinstance(self.immediate, Unset):
            immediate = UNSET
        else:
            immediate = self.immediate

        check_conditions: Union[None, Unset, bool]
        if isinstance(self.check_conditions, Unset):
            check_conditions = UNSET
        else:
            check_conditions = self.check_conditions

        context: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.context, Unset):
            context = self.context.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "alert_id": alert_id,
            }
        )
        if immediate is not UNSET:
            field_dict["immediate"] = immediate
        if check_conditions is not UNSET:
            field_dict["check_conditions"] = check_conditions
        if context is not UNSET:
            field_dict["context"] = context

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.new_workflow_run_data_attributes_type_4_context import NewWorkflowRunDataAttributesType4Context

        d = dict(src_dict)
        alert_id = d.pop("alert_id")

        def _parse_immediate(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        immediate = _parse_immediate(d.pop("immediate", UNSET))

        def _parse_check_conditions(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        check_conditions = _parse_check_conditions(d.pop("check_conditions", UNSET))

        _context = d.pop("context", UNSET)
        context: Union[Unset, NewWorkflowRunDataAttributesType4Context]
        if isinstance(_context, Unset):
            context = UNSET
        else:
            context = NewWorkflowRunDataAttributesType4Context.from_dict(_context)

        new_workflow_run_data_attributes_type_4 = cls(
            alert_id=alert_id,
            immediate=immediate,
            check_conditions=check_conditions,
            context=context,
        )

        new_workflow_run_data_attributes_type_4.additional_properties = d
        return new_workflow_run_data_attributes_type_4

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
