from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.update_form_field_placement_data_attributes_placement_operator import (
    UpdateFormFieldPlacementDataAttributesPlacementOperator,
)
from ..models.update_form_field_placement_data_attributes_required_operator import (
    UpdateFormFieldPlacementDataAttributesRequiredOperator,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateFormFieldPlacementDataAttributes")


@_attrs_define
class UpdateFormFieldPlacementDataAttributes:
    """
    Attributes:
        form_set_id (Union[Unset, str]): The form set this field is placed in.
        form (Union[Unset, str]): The form this field is placed on.
        position (Union[Unset, int]): The position of the field placement.
        required (Union[Unset, bool]): Whether the field is unconditionally required on this form.
        required_operator (Union[Unset, UpdateFormFieldPlacementDataAttributesRequiredOperator]): Logical operator when
            evaluating multiple form_field_placement_conditions with conditioned=required
        placement_operator (Union[Unset, UpdateFormFieldPlacementDataAttributesPlacementOperator]): Logical operator
            when evaluating multiple form_field_placement_conditions with conditioned=placement
    """

    form_set_id: Union[Unset, str] = UNSET
    form: Union[Unset, str] = UNSET
    position: Union[Unset, int] = UNSET
    required: Union[Unset, bool] = UNSET
    required_operator: Union[Unset, UpdateFormFieldPlacementDataAttributesRequiredOperator] = UNSET
    placement_operator: Union[Unset, UpdateFormFieldPlacementDataAttributesPlacementOperator] = UNSET

    def to_dict(self) -> dict[str, Any]:
        form_set_id = self.form_set_id

        form = self.form

        position = self.position

        required = self.required

        required_operator: Union[Unset, str] = UNSET
        if not isinstance(self.required_operator, Unset):
            required_operator = self.required_operator.value

        placement_operator: Union[Unset, str] = UNSET
        if not isinstance(self.placement_operator, Unset):
            placement_operator = self.placement_operator.value

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if form_set_id is not UNSET:
            field_dict["form_set_id"] = form_set_id
        if form is not UNSET:
            field_dict["form"] = form
        if position is not UNSET:
            field_dict["position"] = position
        if required is not UNSET:
            field_dict["required"] = required
        if required_operator is not UNSET:
            field_dict["required_operator"] = required_operator
        if placement_operator is not UNSET:
            field_dict["placement_operator"] = placement_operator

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        form_set_id = d.pop("form_set_id", UNSET)

        form = d.pop("form", UNSET)

        position = d.pop("position", UNSET)

        required = d.pop("required", UNSET)

        _required_operator = d.pop("required_operator", UNSET)
        required_operator: Union[Unset, UpdateFormFieldPlacementDataAttributesRequiredOperator]
        if isinstance(_required_operator, Unset):
            required_operator = UNSET
        else:
            required_operator = UpdateFormFieldPlacementDataAttributesRequiredOperator(_required_operator)

        _placement_operator = d.pop("placement_operator", UNSET)
        placement_operator: Union[Unset, UpdateFormFieldPlacementDataAttributesPlacementOperator]
        if isinstance(_placement_operator, Unset):
            placement_operator = UNSET
        else:
            placement_operator = UpdateFormFieldPlacementDataAttributesPlacementOperator(_placement_operator)

        update_form_field_placement_data_attributes = cls(
            form_set_id=form_set_id,
            form=form,
            position=position,
            required=required,
            required_operator=required_operator,
            placement_operator=placement_operator,
        )

        return update_form_field_placement_data_attributes
