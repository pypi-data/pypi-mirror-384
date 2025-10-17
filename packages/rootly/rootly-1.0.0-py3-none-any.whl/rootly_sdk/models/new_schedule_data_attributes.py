from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.new_schedule_data_attributes_slack_user_group import NewScheduleDataAttributesSlackUserGroup


T = TypeVar("T", bound="NewScheduleDataAttributes")


@_attrs_define
class NewScheduleDataAttributes:
    """
    Attributes:
        name (str): The name of the schedule
        description (Union[None, Unset, str]): The description of the schedule
        all_time_coverage (Union[None, Unset, bool]): 24/7 coverage of the schedule
        slack_user_group (Union[Unset, NewScheduleDataAttributesSlackUserGroup]):
        owner_group_ids (Union[Unset, list[str]]): Owning teams.
        owner_user_id (Union[None, Unset, int]): ID of the owner of the schedule
    """

    name: str
    description: Union[None, Unset, str] = UNSET
    all_time_coverage: Union[None, Unset, bool] = UNSET
    slack_user_group: Union[Unset, "NewScheduleDataAttributesSlackUserGroup"] = UNSET
    owner_group_ids: Union[Unset, list[str]] = UNSET
    owner_user_id: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        all_time_coverage: Union[None, Unset, bool]
        if isinstance(self.all_time_coverage, Unset):
            all_time_coverage = UNSET
        else:
            all_time_coverage = self.all_time_coverage

        slack_user_group: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.slack_user_group, Unset):
            slack_user_group = self.slack_user_group.to_dict()

        owner_group_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.owner_group_ids, Unset):
            owner_group_ids = self.owner_group_ids

        owner_user_id: Union[None, Unset, int]
        if isinstance(self.owner_user_id, Unset):
            owner_user_id = UNSET
        else:
            owner_user_id = self.owner_user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if all_time_coverage is not UNSET:
            field_dict["all_time_coverage"] = all_time_coverage
        if slack_user_group is not UNSET:
            field_dict["slack_user_group"] = slack_user_group
        if owner_group_ids is not UNSET:
            field_dict["owner_group_ids"] = owner_group_ids
        if owner_user_id is not UNSET:
            field_dict["owner_user_id"] = owner_user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.new_schedule_data_attributes_slack_user_group import NewScheduleDataAttributesSlackUserGroup

        d = src_dict.copy()
        name = d.pop("name")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_all_time_coverage(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        all_time_coverage = _parse_all_time_coverage(d.pop("all_time_coverage", UNSET))

        _slack_user_group = d.pop("slack_user_group", UNSET)
        slack_user_group: Union[Unset, NewScheduleDataAttributesSlackUserGroup]
        if isinstance(_slack_user_group, Unset):
            slack_user_group = UNSET
        else:
            slack_user_group = NewScheduleDataAttributesSlackUserGroup.from_dict(_slack_user_group)

        owner_group_ids = cast(list[str], d.pop("owner_group_ids", UNSET))

        def _parse_owner_user_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        owner_user_id = _parse_owner_user_id(d.pop("owner_user_id", UNSET))

        new_schedule_data_attributes = cls(
            name=name,
            description=description,
            all_time_coverage=all_time_coverage,
            slack_user_group=slack_user_group,
            owner_group_ids=owner_group_ids,
            owner_user_id=owner_user_id,
        )

        return new_schedule_data_attributes
