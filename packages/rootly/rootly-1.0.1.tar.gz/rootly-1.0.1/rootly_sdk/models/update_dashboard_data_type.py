from typing import Literal, cast

UpdateDashboardDataType = Literal["dashboards"]

UPDATE_DASHBOARD_DATA_TYPE_VALUES: set[UpdateDashboardDataType] = {
    "dashboards",
}


def check_update_dashboard_data_type(value: str) -> UpdateDashboardDataType:
    if value in UPDATE_DASHBOARD_DATA_TYPE_VALUES:
        return cast(UpdateDashboardDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {UPDATE_DASHBOARD_DATA_TYPE_VALUES!r}")
