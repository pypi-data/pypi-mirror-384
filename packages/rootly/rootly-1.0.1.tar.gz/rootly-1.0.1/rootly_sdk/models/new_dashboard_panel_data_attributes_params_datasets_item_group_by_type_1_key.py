from typing import Literal, cast

NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key = Literal["custom_field", "incident_role"]

NEW_DASHBOARD_PANEL_DATA_ATTRIBUTES_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES: set[
    NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key
] = {
    "custom_field",
    "incident_role",
}


def check_new_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1_key(
    value: str,
) -> NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key:
    if value in NEW_DASHBOARD_PANEL_DATA_ATTRIBUTES_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES:
        return cast(NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {NEW_DASHBOARD_PANEL_DATA_ATTRIBUTES_PARAMS_DATASETS_ITEM_GROUP_BY_TYPE_1_KEY_VALUES!r}"
    )
