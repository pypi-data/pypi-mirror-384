from typing import Literal, cast

UpdateDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key = Literal["custom_field", "incident_role"]

UPDATE_DASHBOARD_PANEL_DATA_ATTRIBUTES_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES: set[
    UpdateDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key
] = {
    "custom_field",
    "incident_role",
}


def check_update_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1_key(
    value: str,
) -> UpdateDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key:
    if value in UPDATE_DASHBOARD_PANEL_DATA_ATTRIBUTES_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES:
        return cast(UpdateDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_DASHBOARD_PANEL_DATA_ATTRIBUTES_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES!r}"
    )
