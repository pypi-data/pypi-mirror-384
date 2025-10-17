from typing import Literal, cast

NewFormSetConditionDataAttributesComparison = Literal["equal"]

NEW_FORM_SET_CONDITION_DATA_ATTRIBUTES_COMPARISON_VALUES: set[NewFormSetConditionDataAttributesComparison] = {
    "equal",
}


def check_new_form_set_condition_data_attributes_comparison(value: str) -> NewFormSetConditionDataAttributesComparison:
    if value in NEW_FORM_SET_CONDITION_DATA_ATTRIBUTES_COMPARISON_VALUES:
        return cast(NewFormSetConditionDataAttributesComparison, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {NEW_FORM_SET_CONDITION_DATA_ATTRIBUTES_COMPARISON_VALUES!r}"
    )
