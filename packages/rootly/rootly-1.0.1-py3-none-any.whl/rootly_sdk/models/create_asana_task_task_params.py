from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_asana_task_task_params_dependency_direction import (
    CreateAsanaTaskTaskParamsDependencyDirection,
    check_create_asana_task_task_params_dependency_direction,
)
from ..models.create_asana_task_task_params_task_type import (
    CreateAsanaTaskTaskParamsTaskType,
    check_create_asana_task_task_params_task_type,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_asana_task_task_params_completion import CreateAsanaTaskTaskParamsCompletion
    from ..models.create_asana_task_task_params_projects_item import CreateAsanaTaskTaskParamsProjectsItem
    from ..models.create_asana_task_task_params_workspace import CreateAsanaTaskTaskParamsWorkspace


T = TypeVar("T", bound="CreateAsanaTaskTaskParams")


@_attrs_define
class CreateAsanaTaskTaskParams:
    """
    Attributes:
        workspace (CreateAsanaTaskTaskParamsWorkspace):
        projects (list['CreateAsanaTaskTaskParamsProjectsItem']):
        title (str): The task title
        completion (CreateAsanaTaskTaskParamsCompletion):
        task_type (Union[Unset, CreateAsanaTaskTaskParamsTaskType]):
        notes (Union[Unset, str]):
        assign_user_email (Union[Unset, str]): The assigned user's email
        due_date (Union[Unset, str]): The due date
        custom_fields_mapping (Union[None, Unset, str]): Custom field mappings. Can contain liquid markup and need to be
            valid JSON
        dependency_direction (Union[Unset, CreateAsanaTaskTaskParamsDependencyDirection]):  Default: 'blocking'.
        dependent_task_ids (Union[None, Unset, list[str]]): Dependent task ids. Supports liquid syntax
    """

    workspace: "CreateAsanaTaskTaskParamsWorkspace"
    projects: list["CreateAsanaTaskTaskParamsProjectsItem"]
    title: str
    completion: "CreateAsanaTaskTaskParamsCompletion"
    task_type: Union[Unset, CreateAsanaTaskTaskParamsTaskType] = UNSET
    notes: Union[Unset, str] = UNSET
    assign_user_email: Union[Unset, str] = UNSET
    due_date: Union[Unset, str] = UNSET
    custom_fields_mapping: Union[None, Unset, str] = UNSET
    dependency_direction: Union[Unset, CreateAsanaTaskTaskParamsDependencyDirection] = "blocking"
    dependent_task_ids: Union[None, Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workspace = self.workspace.to_dict()

        projects = []
        for projects_item_data in self.projects:
            projects_item = projects_item_data.to_dict()
            projects.append(projects_item)

        title = self.title

        completion = self.completion.to_dict()

        task_type: Union[Unset, str] = UNSET
        if not isinstance(self.task_type, Unset):
            task_type = self.task_type

        notes = self.notes

        assign_user_email = self.assign_user_email

        due_date = self.due_date

        custom_fields_mapping: Union[None, Unset, str]
        if isinstance(self.custom_fields_mapping, Unset):
            custom_fields_mapping = UNSET
        else:
            custom_fields_mapping = self.custom_fields_mapping

        dependency_direction: Union[Unset, str] = UNSET
        if not isinstance(self.dependency_direction, Unset):
            dependency_direction = self.dependency_direction

        dependent_task_ids: Union[None, Unset, list[str]]
        if isinstance(self.dependent_task_ids, Unset):
            dependent_task_ids = UNSET
        elif isinstance(self.dependent_task_ids, list):
            dependent_task_ids = self.dependent_task_ids

        else:
            dependent_task_ids = self.dependent_task_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace": workspace,
                "projects": projects,
                "title": title,
                "completion": completion,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type
        if notes is not UNSET:
            field_dict["notes"] = notes
        if assign_user_email is not UNSET:
            field_dict["assign_user_email"] = assign_user_email
        if due_date is not UNSET:
            field_dict["due_date"] = due_date
        if custom_fields_mapping is not UNSET:
            field_dict["custom_fields_mapping"] = custom_fields_mapping
        if dependency_direction is not UNSET:
            field_dict["dependency_direction"] = dependency_direction
        if dependent_task_ids is not UNSET:
            field_dict["dependent_task_ids"] = dependent_task_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_asana_task_task_params_completion import CreateAsanaTaskTaskParamsCompletion
        from ..models.create_asana_task_task_params_projects_item import CreateAsanaTaskTaskParamsProjectsItem
        from ..models.create_asana_task_task_params_workspace import CreateAsanaTaskTaskParamsWorkspace

        d = dict(src_dict)
        workspace = CreateAsanaTaskTaskParamsWorkspace.from_dict(d.pop("workspace"))

        projects = []
        _projects = d.pop("projects")
        for projects_item_data in _projects:
            projects_item = CreateAsanaTaskTaskParamsProjectsItem.from_dict(projects_item_data)

            projects.append(projects_item)

        title = d.pop("title")

        completion = CreateAsanaTaskTaskParamsCompletion.from_dict(d.pop("completion"))

        _task_type = d.pop("task_type", UNSET)
        task_type: Union[Unset, CreateAsanaTaskTaskParamsTaskType]
        if isinstance(_task_type, Unset):
            task_type = UNSET
        else:
            task_type = check_create_asana_task_task_params_task_type(_task_type)

        notes = d.pop("notes", UNSET)

        assign_user_email = d.pop("assign_user_email", UNSET)

        due_date = d.pop("due_date", UNSET)

        def _parse_custom_fields_mapping(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        custom_fields_mapping = _parse_custom_fields_mapping(d.pop("custom_fields_mapping", UNSET))

        _dependency_direction = d.pop("dependency_direction", UNSET)
        dependency_direction: Union[Unset, CreateAsanaTaskTaskParamsDependencyDirection]
        if isinstance(_dependency_direction, Unset):
            dependency_direction = UNSET
        else:
            dependency_direction = check_create_asana_task_task_params_dependency_direction(_dependency_direction)

        def _parse_dependent_task_ids(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                dependent_task_ids_type_0 = cast(list[str], data)

                return dependent_task_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        dependent_task_ids = _parse_dependent_task_ids(d.pop("dependent_task_ids", UNSET))

        create_asana_task_task_params = cls(
            workspace=workspace,
            projects=projects,
            title=title,
            completion=completion,
            task_type=task_type,
            notes=notes,
            assign_user_email=assign_user_email,
            due_date=due_date,
            custom_fields_mapping=custom_fields_mapping,
            dependency_direction=dependency_direction,
            dependent_task_ids=dependent_task_ids,
        )

        create_asana_task_task_params.additional_properties = d
        return create_asana_task_task_params

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
