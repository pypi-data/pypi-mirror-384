from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_dashboard_data_attributes_color import NewDashboardDataAttributesColor
from ..models.new_dashboard_data_attributes_owner import NewDashboardDataAttributesOwner
from ..models.new_dashboard_data_attributes_period import NewDashboardDataAttributesPeriod
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewDashboardDataAttributes")


@_attrs_define
class NewDashboardDataAttributes:
    """
    Attributes:
        name (str): The name of the dashboard
        owner (NewDashboardDataAttributesOwner): The owner type of the dashboard
        description (Union[None, Unset, str]): The description of the dashboard
        public (Union[Unset, bool]): Whether the dashboard is public
        range_ (Union[None, Unset, str]): The date range for dashboard panel data
        auto_refresh (Union[Unset, bool]): Whether the dashboard auto-updates the UI with new data.
        color (Union[Unset, NewDashboardDataAttributesColor]): The hex color of the dashboard
        icon (Union[Unset, str]): The emoji icon of the dashboard
        period (Union[Unset, NewDashboardDataAttributesPeriod]): The grouping period for dashboard panel data
    """

    name: str
    owner: NewDashboardDataAttributesOwner
    description: Union[None, Unset, str] = UNSET
    public: Union[Unset, bool] = UNSET
    range_: Union[None, Unset, str] = UNSET
    auto_refresh: Union[Unset, bool] = UNSET
    color: Union[Unset, NewDashboardDataAttributesColor] = UNSET
    icon: Union[Unset, str] = UNSET
    period: Union[Unset, NewDashboardDataAttributesPeriod] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        owner = self.owner.value

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        public = self.public

        range_: Union[None, Unset, str]
        if isinstance(self.range_, Unset):
            range_ = UNSET
        else:
            range_ = self.range_

        auto_refresh = self.auto_refresh

        color: Union[Unset, str] = UNSET
        if not isinstance(self.color, Unset):
            color = self.color.value

        icon = self.icon

        period: Union[Unset, str] = UNSET
        if not isinstance(self.period, Unset):
            period = self.period.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "owner": owner,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if public is not UNSET:
            field_dict["public"] = public
        if range_ is not UNSET:
            field_dict["range"] = range_
        if auto_refresh is not UNSET:
            field_dict["auto_refresh"] = auto_refresh
        if color is not UNSET:
            field_dict["color"] = color
        if icon is not UNSET:
            field_dict["icon"] = icon
        if period is not UNSET:
            field_dict["period"] = period

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        owner = NewDashboardDataAttributesOwner(d.pop("owner"))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        public = d.pop("public", UNSET)

        def _parse_range_(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        range_ = _parse_range_(d.pop("range", UNSET))

        auto_refresh = d.pop("auto_refresh", UNSET)

        _color = d.pop("color", UNSET)
        color: Union[Unset, NewDashboardDataAttributesColor]
        if isinstance(_color, Unset):
            color = UNSET
        else:
            color = NewDashboardDataAttributesColor(_color)

        icon = d.pop("icon", UNSET)

        _period = d.pop("period", UNSET)
        period: Union[Unset, NewDashboardDataAttributesPeriod]
        if isinstance(_period, Unset):
            period = UNSET
        else:
            period = NewDashboardDataAttributesPeriod(_period)

        new_dashboard_data_attributes = cls(
            name=name,
            owner=owner,
            description=description,
            public=public,
            range_=range_,
            auto_refresh=auto_refresh,
            color=color,
            icon=icon,
            period=period,
        )

        return new_dashboard_data_attributes
