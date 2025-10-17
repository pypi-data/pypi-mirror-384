from typing import Literal, cast

DashboardPanelParamsDatasetsItemGroupByType1Key = Literal["custom_field", "incident_role"]

DASHBOARD_PANEL_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES: set[
    DashboardPanelParamsDatasetsItemGroupByType1Key
] = {
    "custom_field",
    "incident_role",
}


def check_dashboard_panel_params_datasets_item_group_by_type_1_key(
    value: str,
) -> DashboardPanelParamsDatasetsItemGroupByType1Key:
    if value in DASHBOARD_PANEL_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES:
        return cast(DashboardPanelParamsDatasetsItemGroupByType1Key, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {DASHBOARD_PANEL_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES!r}"
    )
