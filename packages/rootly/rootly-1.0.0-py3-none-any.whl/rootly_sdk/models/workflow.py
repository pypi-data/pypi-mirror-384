from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.workflow_repeat_on_type_0_item import WorkflowRepeatOnType0Item
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action_item_trigger_params import ActionItemTriggerParams
    from ..models.alert_trigger_params import AlertTriggerParams
    from ..models.incident_trigger_params import IncidentTriggerParams
    from ..models.pulse_trigger_params import PulseTriggerParams
    from ..models.simple_trigger_params import SimpleTriggerParams


T = TypeVar("T", bound="Workflow")


@_attrs_define
class Workflow:
    """
    Attributes:
        name (str): The title of the workflow
        created_at (str): Date of creation
        updated_at (str): Date of last update
        slug (Union[Unset, str]): The slug of the workflow
        description (Union[None, Unset, str]): The description of the workflow
        command (Union[None, Unset, str]): Workflow command
        command_feedback_enabled (Union[None, Unset, bool]): This will notify you back when the workflow is starting
        wait (Union[None, Unset, str]): Wait this duration before executing
        repeat_every_duration (Union[None, Unset, str]): Repeat workflow every duration
        repeat_condition_duration_since_first_run (Union[None, Unset, str]): The workflow will stop repeating if its
            runtime since it's first workflow run exceeds the duration set in this field
        repeat_condition_number_of_repeats (Union[Unset, int]): The workflow will stop repeating if the number of
            repeats exceeds the value set in this field
        continuously_repeat (Union[Unset, bool]): When continuously repeat is true, repeat workflows aren't
            automatically stopped when conditions aren't met. This setting won't override your conditions set by
            repeat_condition_duration_since_first_run and repeat_condition_number_of_repeats parameters.
        repeat_on (Union[None, Unset, list[WorkflowRepeatOnType0Item]]):
        enabled (Union[Unset, bool]):
        locked (Union[Unset, bool]): Restricts workflow edits to admins when turned on. Only admins can set this field.
        position (Union[Unset, int]): The order which the workflow should run with other workflows.
        workflow_group_id (Union[None, Unset, str]): The group this workflow belongs to.
        trigger_params (Union['ActionItemTriggerParams', 'AlertTriggerParams', 'IncidentTriggerParams',
            'PulseTriggerParams', 'SimpleTriggerParams', Unset]):
        environment_ids (Union[Unset, list[str]]):
        severity_ids (Union[Unset, list[str]]):
        incident_type_ids (Union[Unset, list[str]]):
        incident_role_ids (Union[Unset, list[str]]):
        service_ids (Union[Unset, list[str]]):
        functionality_ids (Union[Unset, list[str]]):
        group_ids (Union[Unset, list[str]]):
        cause_ids (Union[Unset, list[str]]):
        sub_status_ids (Union[Unset, list[str]]):
    """

    name: str
    created_at: str
    updated_at: str
    slug: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    command: Union[None, Unset, str] = UNSET
    command_feedback_enabled: Union[None, Unset, bool] = UNSET
    wait: Union[None, Unset, str] = UNSET
    repeat_every_duration: Union[None, Unset, str] = UNSET
    repeat_condition_duration_since_first_run: Union[None, Unset, str] = UNSET
    repeat_condition_number_of_repeats: Union[Unset, int] = UNSET
    continuously_repeat: Union[Unset, bool] = UNSET
    repeat_on: Union[None, Unset, list[WorkflowRepeatOnType0Item]] = UNSET
    enabled: Union[Unset, bool] = UNSET
    locked: Union[Unset, bool] = UNSET
    position: Union[Unset, int] = UNSET
    workflow_group_id: Union[None, Unset, str] = UNSET
    trigger_params: Union[
        "ActionItemTriggerParams",
        "AlertTriggerParams",
        "IncidentTriggerParams",
        "PulseTriggerParams",
        "SimpleTriggerParams",
        Unset,
    ] = UNSET
    environment_ids: Union[Unset, list[str]] = UNSET
    severity_ids: Union[Unset, list[str]] = UNSET
    incident_type_ids: Union[Unset, list[str]] = UNSET
    incident_role_ids: Union[Unset, list[str]] = UNSET
    service_ids: Union[Unset, list[str]] = UNSET
    functionality_ids: Union[Unset, list[str]] = UNSET
    group_ids: Union[Unset, list[str]] = UNSET
    cause_ids: Union[Unset, list[str]] = UNSET
    sub_status_ids: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.action_item_trigger_params import ActionItemTriggerParams
        from ..models.alert_trigger_params import AlertTriggerParams
        from ..models.incident_trigger_params import IncidentTriggerParams
        from ..models.pulse_trigger_params import PulseTriggerParams

        name = self.name

        created_at = self.created_at

        updated_at = self.updated_at

        slug = self.slug

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        command: Union[None, Unset, str]
        if isinstance(self.command, Unset):
            command = UNSET
        else:
            command = self.command

        command_feedback_enabled: Union[None, Unset, bool]
        if isinstance(self.command_feedback_enabled, Unset):
            command_feedback_enabled = UNSET
        else:
            command_feedback_enabled = self.command_feedback_enabled

        wait: Union[None, Unset, str]
        if isinstance(self.wait, Unset):
            wait = UNSET
        else:
            wait = self.wait

        repeat_every_duration: Union[None, Unset, str]
        if isinstance(self.repeat_every_duration, Unset):
            repeat_every_duration = UNSET
        else:
            repeat_every_duration = self.repeat_every_duration

        repeat_condition_duration_since_first_run: Union[None, Unset, str]
        if isinstance(self.repeat_condition_duration_since_first_run, Unset):
            repeat_condition_duration_since_first_run = UNSET
        else:
            repeat_condition_duration_since_first_run = self.repeat_condition_duration_since_first_run

        repeat_condition_number_of_repeats = self.repeat_condition_number_of_repeats

        continuously_repeat = self.continuously_repeat

        repeat_on: Union[None, Unset, list[str]]
        if isinstance(self.repeat_on, Unset):
            repeat_on = UNSET
        elif isinstance(self.repeat_on, list):
            repeat_on = []
            for repeat_on_type_0_item_data in self.repeat_on:
                repeat_on_type_0_item = repeat_on_type_0_item_data.value
                repeat_on.append(repeat_on_type_0_item)

        else:
            repeat_on = self.repeat_on

        enabled = self.enabled

        locked = self.locked

        position = self.position

        workflow_group_id: Union[None, Unset, str]
        if isinstance(self.workflow_group_id, Unset):
            workflow_group_id = UNSET
        else:
            workflow_group_id = self.workflow_group_id

        trigger_params: Union[Unset, dict[str, Any]]
        if isinstance(self.trigger_params, Unset):
            trigger_params = UNSET
        elif isinstance(self.trigger_params, IncidentTriggerParams):
            trigger_params = self.trigger_params.to_dict()
        elif isinstance(self.trigger_params, ActionItemTriggerParams):
            trigger_params = self.trigger_params.to_dict()
        elif isinstance(self.trigger_params, AlertTriggerParams):
            trigger_params = self.trigger_params.to_dict()
        elif isinstance(self.trigger_params, PulseTriggerParams):
            trigger_params = self.trigger_params.to_dict()
        else:
            trigger_params = self.trigger_params.to_dict()

        environment_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.environment_ids, Unset):
            environment_ids = self.environment_ids

        severity_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.severity_ids, Unset):
            severity_ids = self.severity_ids

        incident_type_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_type_ids, Unset):
            incident_type_ids = self.incident_type_ids

        incident_role_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_role_ids, Unset):
            incident_role_ids = self.incident_role_ids

        service_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.service_ids, Unset):
            service_ids = self.service_ids

        functionality_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.functionality_ids, Unset):
            functionality_ids = self.functionality_ids

        group_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.group_ids, Unset):
            group_ids = self.group_ids

        cause_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.cause_ids, Unset):
            cause_ids = self.cause_ids

        sub_status_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.sub_status_ids, Unset):
            sub_status_ids = self.sub_status_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
        if description is not UNSET:
            field_dict["description"] = description
        if command is not UNSET:
            field_dict["command"] = command
        if command_feedback_enabled is not UNSET:
            field_dict["command_feedback_enabled"] = command_feedback_enabled
        if wait is not UNSET:
            field_dict["wait"] = wait
        if repeat_every_duration is not UNSET:
            field_dict["repeat_every_duration"] = repeat_every_duration
        if repeat_condition_duration_since_first_run is not UNSET:
            field_dict["repeat_condition_duration_since_first_run"] = repeat_condition_duration_since_first_run
        if repeat_condition_number_of_repeats is not UNSET:
            field_dict["repeat_condition_number_of_repeats"] = repeat_condition_number_of_repeats
        if continuously_repeat is not UNSET:
            field_dict["continuously_repeat"] = continuously_repeat
        if repeat_on is not UNSET:
            field_dict["repeat_on"] = repeat_on
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if locked is not UNSET:
            field_dict["locked"] = locked
        if position is not UNSET:
            field_dict["position"] = position
        if workflow_group_id is not UNSET:
            field_dict["workflow_group_id"] = workflow_group_id
        if trigger_params is not UNSET:
            field_dict["trigger_params"] = trigger_params
        if environment_ids is not UNSET:
            field_dict["environment_ids"] = environment_ids
        if severity_ids is not UNSET:
            field_dict["severity_ids"] = severity_ids
        if incident_type_ids is not UNSET:
            field_dict["incident_type_ids"] = incident_type_ids
        if incident_role_ids is not UNSET:
            field_dict["incident_role_ids"] = incident_role_ids
        if service_ids is not UNSET:
            field_dict["service_ids"] = service_ids
        if functionality_ids is not UNSET:
            field_dict["functionality_ids"] = functionality_ids
        if group_ids is not UNSET:
            field_dict["group_ids"] = group_ids
        if cause_ids is not UNSET:
            field_dict["cause_ids"] = cause_ids
        if sub_status_ids is not UNSET:
            field_dict["sub_status_ids"] = sub_status_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.action_item_trigger_params import ActionItemTriggerParams
        from ..models.alert_trigger_params import AlertTriggerParams
        from ..models.incident_trigger_params import IncidentTriggerParams
        from ..models.pulse_trigger_params import PulseTriggerParams
        from ..models.simple_trigger_params import SimpleTriggerParams

        d = src_dict.copy()
        name = d.pop("name")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        slug = d.pop("slug", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_command(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        command = _parse_command(d.pop("command", UNSET))

        def _parse_command_feedback_enabled(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        command_feedback_enabled = _parse_command_feedback_enabled(d.pop("command_feedback_enabled", UNSET))

        def _parse_wait(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        wait = _parse_wait(d.pop("wait", UNSET))

        def _parse_repeat_every_duration(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        repeat_every_duration = _parse_repeat_every_duration(d.pop("repeat_every_duration", UNSET))

        def _parse_repeat_condition_duration_since_first_run(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        repeat_condition_duration_since_first_run = _parse_repeat_condition_duration_since_first_run(
            d.pop("repeat_condition_duration_since_first_run", UNSET)
        )

        repeat_condition_number_of_repeats = d.pop("repeat_condition_number_of_repeats", UNSET)

        continuously_repeat = d.pop("continuously_repeat", UNSET)

        def _parse_repeat_on(data: object) -> Union[None, Unset, list[WorkflowRepeatOnType0Item]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                repeat_on_type_0 = []
                _repeat_on_type_0 = data
                for repeat_on_type_0_item_data in _repeat_on_type_0:
                    repeat_on_type_0_item = WorkflowRepeatOnType0Item(repeat_on_type_0_item_data)

                    repeat_on_type_0.append(repeat_on_type_0_item)

                return repeat_on_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[WorkflowRepeatOnType0Item]], data)

        repeat_on = _parse_repeat_on(d.pop("repeat_on", UNSET))

        enabled = d.pop("enabled", UNSET)

        locked = d.pop("locked", UNSET)

        position = d.pop("position", UNSET)

        def _parse_workflow_group_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        workflow_group_id = _parse_workflow_group_id(d.pop("workflow_group_id", UNSET))

        def _parse_trigger_params(
            data: object,
        ) -> Union[
            "ActionItemTriggerParams",
            "AlertTriggerParams",
            "IncidentTriggerParams",
            "PulseTriggerParams",
            "SimpleTriggerParams",
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                trigger_params_type_0 = IncidentTriggerParams.from_dict(data)

                return trigger_params_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                trigger_params_type_1 = ActionItemTriggerParams.from_dict(data)

                return trigger_params_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                trigger_params_type_2 = AlertTriggerParams.from_dict(data)

                return trigger_params_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                trigger_params_type_3 = PulseTriggerParams.from_dict(data)

                return trigger_params_type_3
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            trigger_params_type_4 = SimpleTriggerParams.from_dict(data)

            return trigger_params_type_4

        trigger_params = _parse_trigger_params(d.pop("trigger_params", UNSET))

        environment_ids = cast(list[str], d.pop("environment_ids", UNSET))

        severity_ids = cast(list[str], d.pop("severity_ids", UNSET))

        incident_type_ids = cast(list[str], d.pop("incident_type_ids", UNSET))

        incident_role_ids = cast(list[str], d.pop("incident_role_ids", UNSET))

        service_ids = cast(list[str], d.pop("service_ids", UNSET))

        functionality_ids = cast(list[str], d.pop("functionality_ids", UNSET))

        group_ids = cast(list[str], d.pop("group_ids", UNSET))

        cause_ids = cast(list[str], d.pop("cause_ids", UNSET))

        sub_status_ids = cast(list[str], d.pop("sub_status_ids", UNSET))

        workflow = cls(
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            slug=slug,
            description=description,
            command=command,
            command_feedback_enabled=command_feedback_enabled,
            wait=wait,
            repeat_every_duration=repeat_every_duration,
            repeat_condition_duration_since_first_run=repeat_condition_duration_since_first_run,
            repeat_condition_number_of_repeats=repeat_condition_number_of_repeats,
            continuously_repeat=continuously_repeat,
            repeat_on=repeat_on,
            enabled=enabled,
            locked=locked,
            position=position,
            workflow_group_id=workflow_group_id,
            trigger_params=trigger_params,
            environment_ids=environment_ids,
            severity_ids=severity_ids,
            incident_type_ids=incident_type_ids,
            incident_role_ids=incident_role_ids,
            service_ids=service_ids,
            functionality_ids=functionality_ids,
            group_ids=group_ids,
            cause_ids=cause_ids,
            sub_status_ids=sub_status_ids,
        )

        workflow.additional_properties = d
        return workflow

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
