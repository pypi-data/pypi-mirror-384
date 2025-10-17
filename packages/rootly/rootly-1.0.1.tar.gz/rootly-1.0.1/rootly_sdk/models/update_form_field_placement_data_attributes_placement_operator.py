from typing import Literal, cast

UpdateFormFieldPlacementDataAttributesPlacementOperator = Literal["and", "or"]

UPDATE_FORM_FIELD_PLACEMENT_DATA_ATTRIBUTES_PLACEMENT_OPERATOR_VALUES: set[
    UpdateFormFieldPlacementDataAttributesPlacementOperator
] = {
    "and",
    "or",
}


def check_update_form_field_placement_data_attributes_placement_operator(
    value: str,
) -> UpdateFormFieldPlacementDataAttributesPlacementOperator:
    if value in UPDATE_FORM_FIELD_PLACEMENT_DATA_ATTRIBUTES_PLACEMENT_OPERATOR_VALUES:
        return cast(UpdateFormFieldPlacementDataAttributesPlacementOperator, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_FORM_FIELD_PLACEMENT_DATA_ATTRIBUTES_PLACEMENT_OPERATOR_VALUES!r}"
    )
