from typing import Literal, cast

FormSetConditionComparison = Literal["equal"]

FORM_SET_CONDITION_COMPARISON_VALUES: set[FormSetConditionComparison] = {
    "equal",
}


def check_form_set_condition_comparison(value: str) -> FormSetConditionComparison:
    if value in FORM_SET_CONDITION_COMPARISON_VALUES:
        return cast(FormSetConditionComparison, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {FORM_SET_CONDITION_COMPARISON_VALUES!r}")
