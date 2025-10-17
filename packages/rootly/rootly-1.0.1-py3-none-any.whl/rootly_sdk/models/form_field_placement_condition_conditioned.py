from typing import Literal, cast

FormFieldPlacementConditionConditioned = Literal["placement", "required"]

FORM_FIELD_PLACEMENT_CONDITION_CONDITIONED_VALUES: set[FormFieldPlacementConditionConditioned] = {
    "placement",
    "required",
}


def check_form_field_placement_condition_conditioned(value: str) -> FormFieldPlacementConditionConditioned:
    if value in FORM_FIELD_PLACEMENT_CONDITION_CONDITIONED_VALUES:
        return cast(FormFieldPlacementConditionConditioned, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {FORM_FIELD_PLACEMENT_CONDITION_CONDITIONED_VALUES!r}"
    )
