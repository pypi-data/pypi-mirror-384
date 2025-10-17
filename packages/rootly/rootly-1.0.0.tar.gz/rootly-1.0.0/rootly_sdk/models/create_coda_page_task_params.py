from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_coda_page_task_params_task_type import CreateCodaPageTaskParamsTaskType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_coda_page_task_params_template import CreateCodaPageTaskParamsTemplate


T = TypeVar("T", bound="CreateCodaPageTaskParams")


@_attrs_define
class CreateCodaPageTaskParams:
    """
    Attributes:
        title (str): The Coda page title
        task_type (Union[Unset, CreateCodaPageTaskParamsTaskType]):
        post_mortem_template_id (Union[Unset, str]): Retrospective template to use when creating page, if desired
        mark_post_mortem_as_published (Union[Unset, bool]):  Default: True.
        subtitle (Union[Unset, str]): The Coda page subtitle
        content (Union[Unset, str]): The Coda page content
        template (Union[Unset, CreateCodaPageTaskParamsTemplate]):
        folder_id (Union[Unset, str]): The Coda folder id
    """

    title: str
    task_type: Union[Unset, CreateCodaPageTaskParamsTaskType] = UNSET
    post_mortem_template_id: Union[Unset, str] = UNSET
    mark_post_mortem_as_published: Union[Unset, bool] = True
    subtitle: Union[Unset, str] = UNSET
    content: Union[Unset, str] = UNSET
    template: Union[Unset, "CreateCodaPageTaskParamsTemplate"] = UNSET
    folder_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title = self.title

        task_type: Union[Unset, str] = UNSET
        if not isinstance(self.task_type, Unset):
            task_type = self.task_type.value

        post_mortem_template_id = self.post_mortem_template_id

        mark_post_mortem_as_published = self.mark_post_mortem_as_published

        subtitle = self.subtitle

        content = self.content

        template: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.template, Unset):
            template = self.template.to_dict()

        folder_id = self.folder_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type
        if post_mortem_template_id is not UNSET:
            field_dict["post_mortem_template_id"] = post_mortem_template_id
        if mark_post_mortem_as_published is not UNSET:
            field_dict["mark_post_mortem_as_published"] = mark_post_mortem_as_published
        if subtitle is not UNSET:
            field_dict["subtitle"] = subtitle
        if content is not UNSET:
            field_dict["content"] = content
        if template is not UNSET:
            field_dict["template"] = template
        if folder_id is not UNSET:
            field_dict["folder_id"] = folder_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.create_coda_page_task_params_template import CreateCodaPageTaskParamsTemplate

        d = src_dict.copy()
        title = d.pop("title")

        _task_type = d.pop("task_type", UNSET)
        task_type: Union[Unset, CreateCodaPageTaskParamsTaskType]
        if isinstance(_task_type, Unset):
            task_type = UNSET
        else:
            task_type = CreateCodaPageTaskParamsTaskType(_task_type)

        post_mortem_template_id = d.pop("post_mortem_template_id", UNSET)

        mark_post_mortem_as_published = d.pop("mark_post_mortem_as_published", UNSET)

        subtitle = d.pop("subtitle", UNSET)

        content = d.pop("content", UNSET)

        _template = d.pop("template", UNSET)
        template: Union[Unset, CreateCodaPageTaskParamsTemplate]
        if isinstance(_template, Unset):
            template = UNSET
        else:
            template = CreateCodaPageTaskParamsTemplate.from_dict(_template)

        folder_id = d.pop("folder_id", UNSET)

        create_coda_page_task_params = cls(
            title=title,
            task_type=task_type,
            post_mortem_template_id=post_mortem_template_id,
            mark_post_mortem_as_published=mark_post_mortem_as_published,
            subtitle=subtitle,
            content=content,
            template=template,
            folder_id=folder_id,
        )

        create_coda_page_task_params.additional_properties = d
        return create_coda_page_task_params

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
