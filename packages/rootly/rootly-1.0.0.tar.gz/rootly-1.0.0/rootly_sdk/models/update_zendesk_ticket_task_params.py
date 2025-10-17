from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_zendesk_ticket_task_params_task_type import UpdateZendeskTicketTaskParamsTaskType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_zendesk_ticket_task_params_completion import UpdateZendeskTicketTaskParamsCompletion
    from ..models.update_zendesk_ticket_task_params_priority import UpdateZendeskTicketTaskParamsPriority


T = TypeVar("T", bound="UpdateZendeskTicketTaskParams")


@_attrs_define
class UpdateZendeskTicketTaskParams:
    """
    Attributes:
        ticket_id (str): The ticket id
        task_type (Union[Unset, UpdateZendeskTicketTaskParamsTaskType]):
        subject (Union[Unset, str]): The ticket subject
        tags (Union[Unset, str]): The ticket tags
        priority (Union[Unset, UpdateZendeskTicketTaskParamsPriority]): The priority id and display name
        completion (Union[Unset, UpdateZendeskTicketTaskParamsCompletion]): The completion id and display name
        custom_fields_mapping (Union[None, Unset, str]): Custom field mappings. Can contain liquid markup and need to be
            valid JSON
        ticket_payload (Union[None, Unset, str]): Additional Zendesk ticket attributes. Will be merged into whatever was
            specified in this tasks current parameters. Can contain liquid markup and need to be valid JSON
    """

    ticket_id: str
    task_type: Union[Unset, UpdateZendeskTicketTaskParamsTaskType] = UNSET
    subject: Union[Unset, str] = UNSET
    tags: Union[Unset, str] = UNSET
    priority: Union[Unset, "UpdateZendeskTicketTaskParamsPriority"] = UNSET
    completion: Union[Unset, "UpdateZendeskTicketTaskParamsCompletion"] = UNSET
    custom_fields_mapping: Union[None, Unset, str] = UNSET
    ticket_payload: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ticket_id = self.ticket_id

        task_type: Union[Unset, str] = UNSET
        if not isinstance(self.task_type, Unset):
            task_type = self.task_type.value

        subject = self.subject

        tags = self.tags

        priority: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.priority, Unset):
            priority = self.priority.to_dict()

        completion: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.completion, Unset):
            completion = self.completion.to_dict()

        custom_fields_mapping: Union[None, Unset, str]
        if isinstance(self.custom_fields_mapping, Unset):
            custom_fields_mapping = UNSET
        else:
            custom_fields_mapping = self.custom_fields_mapping

        ticket_payload: Union[None, Unset, str]
        if isinstance(self.ticket_payload, Unset):
            ticket_payload = UNSET
        else:
            ticket_payload = self.ticket_payload

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ticket_id": ticket_id,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type
        if subject is not UNSET:
            field_dict["subject"] = subject
        if tags is not UNSET:
            field_dict["tags"] = tags
        if priority is not UNSET:
            field_dict["priority"] = priority
        if completion is not UNSET:
            field_dict["completion"] = completion
        if custom_fields_mapping is not UNSET:
            field_dict["custom_fields_mapping"] = custom_fields_mapping
        if ticket_payload is not UNSET:
            field_dict["ticket_payload"] = ticket_payload

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.update_zendesk_ticket_task_params_completion import UpdateZendeskTicketTaskParamsCompletion
        from ..models.update_zendesk_ticket_task_params_priority import UpdateZendeskTicketTaskParamsPriority

        d = src_dict.copy()
        ticket_id = d.pop("ticket_id")

        _task_type = d.pop("task_type", UNSET)
        task_type: Union[Unset, UpdateZendeskTicketTaskParamsTaskType]
        if isinstance(_task_type, Unset):
            task_type = UNSET
        else:
            task_type = UpdateZendeskTicketTaskParamsTaskType(_task_type)

        subject = d.pop("subject", UNSET)

        tags = d.pop("tags", UNSET)

        _priority = d.pop("priority", UNSET)
        priority: Union[Unset, UpdateZendeskTicketTaskParamsPriority]
        if isinstance(_priority, Unset):
            priority = UNSET
        else:
            priority = UpdateZendeskTicketTaskParamsPriority.from_dict(_priority)

        _completion = d.pop("completion", UNSET)
        completion: Union[Unset, UpdateZendeskTicketTaskParamsCompletion]
        if isinstance(_completion, Unset):
            completion = UNSET
        else:
            completion = UpdateZendeskTicketTaskParamsCompletion.from_dict(_completion)

        def _parse_custom_fields_mapping(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        custom_fields_mapping = _parse_custom_fields_mapping(d.pop("custom_fields_mapping", UNSET))

        def _parse_ticket_payload(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ticket_payload = _parse_ticket_payload(d.pop("ticket_payload", UNSET))

        update_zendesk_ticket_task_params = cls(
            ticket_id=ticket_id,
            task_type=task_type,
            subject=subject,
            tags=tags,
            priority=priority,
            completion=completion,
            custom_fields_mapping=custom_fields_mapping,
            ticket_payload=ticket_payload,
        )

        update_zendesk_ticket_task_params.additional_properties = d
        return update_zendesk_ticket_task_params

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
