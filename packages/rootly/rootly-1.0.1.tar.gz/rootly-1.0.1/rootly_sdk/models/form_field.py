from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.form_field_input_kind import FormFieldInputKind, check_form_field_input_kind
from ..models.form_field_kind import FormFieldKind, check_form_field_kind
from ..models.form_field_value_kind import FormFieldValueKind, check_form_field_value_kind
from ..types import UNSET, Unset

T = TypeVar("T", bound="FormField")


@_attrs_define
class FormField:
    """
    Attributes:
        kind (FormFieldKind): The kind of the form field
        input_kind (FormFieldInputKind): The input kind of the form field
        value_kind (FormFieldValueKind): The value kind of the form field
        name (str): The name of the form field
        slug (str): The slug of the form field
        shown (list[str]):
        required (list[str]):
        default_values (list[str]):
        created_at (str): Date of creation
        updated_at (str): Date of last update
        value_kind_catalog_id (Union[None, Unset, str]): The ID of the catalog used when value_kind is `catalog_entity`
        description (Union[None, Unset, str]): The description of the form field
        show_on_incident_details (Union[Unset, bool]): Whether the form field is shown on the incident details panel
        enabled (Union[Unset, bool]): Whether the form field is enabled
    """

    kind: FormFieldKind
    input_kind: FormFieldInputKind
    value_kind: FormFieldValueKind
    name: str
    slug: str
    shown: list[str]
    required: list[str]
    default_values: list[str]
    created_at: str
    updated_at: str
    value_kind_catalog_id: Union[None, Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    show_on_incident_details: Union[Unset, bool] = UNSET
    enabled: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kind: str = self.kind

        input_kind: str = self.input_kind

        value_kind: str = self.value_kind

        name = self.name

        slug = self.slug

        shown = self.shown

        required = self.required

        default_values = self.default_values

        created_at = self.created_at

        updated_at = self.updated_at

        value_kind_catalog_id: Union[None, Unset, str]
        if isinstance(self.value_kind_catalog_id, Unset):
            value_kind_catalog_id = UNSET
        else:
            value_kind_catalog_id = self.value_kind_catalog_id

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        show_on_incident_details = self.show_on_incident_details

        enabled = self.enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "kind": kind,
                "input_kind": input_kind,
                "value_kind": value_kind,
                "name": name,
                "slug": slug,
                "shown": shown,
                "required": required,
                "default_values": default_values,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if value_kind_catalog_id is not UNSET:
            field_dict["value_kind_catalog_id"] = value_kind_catalog_id
        if description is not UNSET:
            field_dict["description"] = description
        if show_on_incident_details is not UNSET:
            field_dict["show_on_incident_details"] = show_on_incident_details
        if enabled is not UNSET:
            field_dict["enabled"] = enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kind = check_form_field_kind(d.pop("kind"))

        input_kind = check_form_field_input_kind(d.pop("input_kind"))

        value_kind = check_form_field_value_kind(d.pop("value_kind"))

        name = d.pop("name")

        slug = d.pop("slug")

        shown = cast(list[str], d.pop("shown"))

        required = cast(list[str], d.pop("required"))

        default_values = cast(list[str], d.pop("default_values"))

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        def _parse_value_kind_catalog_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        value_kind_catalog_id = _parse_value_kind_catalog_id(d.pop("value_kind_catalog_id", UNSET))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        show_on_incident_details = d.pop("show_on_incident_details", UNSET)

        enabled = d.pop("enabled", UNSET)

        form_field = cls(
            kind=kind,
            input_kind=input_kind,
            value_kind=value_kind,
            name=name,
            slug=slug,
            shown=shown,
            required=required,
            default_values=default_values,
            created_at=created_at,
            updated_at=updated_at,
            value_kind_catalog_id=value_kind_catalog_id,
            description=description,
            show_on_incident_details=show_on_incident_details,
            enabled=enabled,
        )

        form_field.additional_properties = d
        return form_field

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
