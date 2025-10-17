from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateIncidentFormFieldSelectionDataAttributes")


@_attrs_define
class UpdateIncidentFormFieldSelectionDataAttributes:
    """
    Attributes:
        value (Union[None, Unset, str]): The selected value for text kind custom fields
        selected_catalog_entity_ids (Union[Unset, list[str]]):
        selected_group_ids (Union[Unset, list[str]]):
        selected_option_ids (Union[Unset, list[str]]):
        selected_service_ids (Union[Unset, list[str]]):
        selected_functionality_ids (Union[Unset, list[str]]):
        selected_user_ids (Union[Unset, list[int]]):
    """

    value: Union[None, Unset, str] = UNSET
    selected_catalog_entity_ids: Union[Unset, list[str]] = UNSET
    selected_group_ids: Union[Unset, list[str]] = UNSET
    selected_option_ids: Union[Unset, list[str]] = UNSET
    selected_service_ids: Union[Unset, list[str]] = UNSET
    selected_functionality_ids: Union[Unset, list[str]] = UNSET
    selected_user_ids: Union[Unset, list[int]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        value: Union[None, Unset, str]
        if isinstance(self.value, Unset):
            value = UNSET
        else:
            value = self.value

        selected_catalog_entity_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.selected_catalog_entity_ids, Unset):
            selected_catalog_entity_ids = self.selected_catalog_entity_ids

        selected_group_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.selected_group_ids, Unset):
            selected_group_ids = self.selected_group_ids

        selected_option_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.selected_option_ids, Unset):
            selected_option_ids = self.selected_option_ids

        selected_service_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.selected_service_ids, Unset):
            selected_service_ids = self.selected_service_ids

        selected_functionality_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.selected_functionality_ids, Unset):
            selected_functionality_ids = self.selected_functionality_ids

        selected_user_ids: Union[Unset, list[int]] = UNSET
        if not isinstance(self.selected_user_ids, Unset):
            selected_user_ids = self.selected_user_ids

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if value is not UNSET:
            field_dict["value"] = value
        if selected_catalog_entity_ids is not UNSET:
            field_dict["selected_catalog_entity_ids"] = selected_catalog_entity_ids
        if selected_group_ids is not UNSET:
            field_dict["selected_group_ids"] = selected_group_ids
        if selected_option_ids is not UNSET:
            field_dict["selected_option_ids"] = selected_option_ids
        if selected_service_ids is not UNSET:
            field_dict["selected_service_ids"] = selected_service_ids
        if selected_functionality_ids is not UNSET:
            field_dict["selected_functionality_ids"] = selected_functionality_ids
        if selected_user_ids is not UNSET:
            field_dict["selected_user_ids"] = selected_user_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()

        def _parse_value(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        value = _parse_value(d.pop("value", UNSET))

        selected_catalog_entity_ids = cast(list[str], d.pop("selected_catalog_entity_ids", UNSET))

        selected_group_ids = cast(list[str], d.pop("selected_group_ids", UNSET))

        selected_option_ids = cast(list[str], d.pop("selected_option_ids", UNSET))

        selected_service_ids = cast(list[str], d.pop("selected_service_ids", UNSET))

        selected_functionality_ids = cast(list[str], d.pop("selected_functionality_ids", UNSET))

        selected_user_ids = cast(list[int], d.pop("selected_user_ids", UNSET))

        update_incident_form_field_selection_data_attributes = cls(
            value=value,
            selected_catalog_entity_ids=selected_catalog_entity_ids,
            selected_group_ids=selected_group_ids,
            selected_option_ids=selected_option_ids,
            selected_service_ids=selected_service_ids,
            selected_functionality_ids=selected_functionality_ids,
            selected_user_ids=selected_user_ids,
        )

        return update_incident_form_field_selection_data_attributes
