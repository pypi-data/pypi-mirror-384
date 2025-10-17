from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_form_field_data_attributes_input_kind import UpdateFormFieldDataAttributesInputKind
from ..models.update_form_field_data_attributes_kind import UpdateFormFieldDataAttributesKind
from ..models.update_form_field_data_attributes_value_kind import UpdateFormFieldDataAttributesValueKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateFormFieldDataAttributes")


@_attrs_define
class UpdateFormFieldDataAttributes:
    """
    Attributes:
        kind (Union[Unset, UpdateFormFieldDataAttributesKind]): The kind of the form field
        input_kind (Union[Unset, UpdateFormFieldDataAttributesInputKind]): The input kind of the form field
        value_kind (Union[Unset, UpdateFormFieldDataAttributesValueKind]): The value kind of the form field
        value_kind_catalog_id (Union[None, Unset, str]): The ID of the catalog used when value_kind is `catalog_entity`
        name (Union[Unset, str]): The name of the form field
        description (Union[None, Unset, str]): The description of the form field
        shown (Union[Unset, list[str]]):
        required (Union[Unset, list[str]]):
        show_on_incident_details (Union[Unset, bool]): Whether the form field is shown on the incident details panel
        enabled (Union[Unset, bool]): Whether the form field is enabled
        default_values (Union[Unset, list[str]]):
    """

    kind: Union[Unset, UpdateFormFieldDataAttributesKind] = UNSET
    input_kind: Union[Unset, UpdateFormFieldDataAttributesInputKind] = UNSET
    value_kind: Union[Unset, UpdateFormFieldDataAttributesValueKind] = UNSET
    value_kind_catalog_id: Union[None, Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    shown: Union[Unset, list[str]] = UNSET
    required: Union[Unset, list[str]] = UNSET
    show_on_incident_details: Union[Unset, bool] = UNSET
    enabled: Union[Unset, bool] = UNSET
    default_values: Union[Unset, list[str]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        kind: Union[Unset, str] = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        input_kind: Union[Unset, str] = UNSET
        if not isinstance(self.input_kind, Unset):
            input_kind = self.input_kind.value

        value_kind: Union[Unset, str] = UNSET
        if not isinstance(self.value_kind, Unset):
            value_kind = self.value_kind.value

        value_kind_catalog_id: Union[None, Unset, str]
        if isinstance(self.value_kind_catalog_id, Unset):
            value_kind_catalog_id = UNSET
        else:
            value_kind_catalog_id = self.value_kind_catalog_id

        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        shown: Union[Unset, list[str]] = UNSET
        if not isinstance(self.shown, Unset):
            shown = self.shown

        required: Union[Unset, list[str]] = UNSET
        if not isinstance(self.required, Unset):
            required = self.required

        show_on_incident_details = self.show_on_incident_details

        enabled = self.enabled

        default_values: Union[Unset, list[str]] = UNSET
        if not isinstance(self.default_values, Unset):
            default_values = self.default_values

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if kind is not UNSET:
            field_dict["kind"] = kind
        if input_kind is not UNSET:
            field_dict["input_kind"] = input_kind
        if value_kind is not UNSET:
            field_dict["value_kind"] = value_kind
        if value_kind_catalog_id is not UNSET:
            field_dict["value_kind_catalog_id"] = value_kind_catalog_id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if shown is not UNSET:
            field_dict["shown"] = shown
        if required is not UNSET:
            field_dict["required"] = required
        if show_on_incident_details is not UNSET:
            field_dict["show_on_incident_details"] = show_on_incident_details
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if default_values is not UNSET:
            field_dict["default_values"] = default_values

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        _kind = d.pop("kind", UNSET)
        kind: Union[Unset, UpdateFormFieldDataAttributesKind]
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = UpdateFormFieldDataAttributesKind(_kind)

        _input_kind = d.pop("input_kind", UNSET)
        input_kind: Union[Unset, UpdateFormFieldDataAttributesInputKind]
        if isinstance(_input_kind, Unset):
            input_kind = UNSET
        else:
            input_kind = UpdateFormFieldDataAttributesInputKind(_input_kind)

        _value_kind = d.pop("value_kind", UNSET)
        value_kind: Union[Unset, UpdateFormFieldDataAttributesValueKind]
        if isinstance(_value_kind, Unset):
            value_kind = UNSET
        else:
            value_kind = UpdateFormFieldDataAttributesValueKind(_value_kind)

        def _parse_value_kind_catalog_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        value_kind_catalog_id = _parse_value_kind_catalog_id(d.pop("value_kind_catalog_id", UNSET))

        name = d.pop("name", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        shown = cast(list[str], d.pop("shown", UNSET))

        required = cast(list[str], d.pop("required", UNSET))

        show_on_incident_details = d.pop("show_on_incident_details", UNSET)

        enabled = d.pop("enabled", UNSET)

        default_values = cast(list[str], d.pop("default_values", UNSET))

        update_form_field_data_attributes = cls(
            kind=kind,
            input_kind=input_kind,
            value_kind=value_kind,
            value_kind_catalog_id=value_kind_catalog_id,
            name=name,
            description=description,
            shown=shown,
            required=required,
            show_on_incident_details=show_on_incident_details,
            enabled=enabled,
            default_values=default_values,
        )

        return update_form_field_data_attributes
