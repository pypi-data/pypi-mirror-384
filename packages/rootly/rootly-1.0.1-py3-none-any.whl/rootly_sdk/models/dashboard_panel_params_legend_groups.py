from typing import Literal, cast

DashboardPanelParamsLegendGroups = Literal["all", "charted"]

DASHBOARD_PANEL_PARAMS_LEGEND_GROUPS_VALUES: set[DashboardPanelParamsLegendGroups] = {
    "all",
    "charted",
}


def check_dashboard_panel_params_legend_groups(value: str) -> DashboardPanelParamsLegendGroups:
    if value in DASHBOARD_PANEL_PARAMS_LEGEND_GROUPS_VALUES:
        return cast(DashboardPanelParamsLegendGroups, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {DASHBOARD_PANEL_PARAMS_LEGEND_GROUPS_VALUES!r}")
