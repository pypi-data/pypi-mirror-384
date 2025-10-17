from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.new_escalation_policy_level_data_attributes_notification_target_params_item_type_0_team_members import (
    NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0TeamMembers,
)
from ..models.new_escalation_policy_level_data_attributes_notification_target_params_item_type_0_type import (
    NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0")


@_attrs_define
class NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0:
    """
    Attributes:
        id (str): The ID of notification target. If Slack channel, then id of the slack channel (eg. C06Q2JK7RQW)
        type_ (NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type): The type of the
            notification target
        team_members (Union[Unset, NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0TeamMembers]):
            For targets with type=team, controls whether to notify admins, all team members, or escalate to team EP.
    """

    id: str
    type_: NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type
    team_members: Union[Unset, NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0TeamMembers] = (
        UNSET
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_.value

        team_members: Union[Unset, str] = UNSET
        if not isinstance(self.team_members, Unset):
            team_members = self.team_members.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
            }
        )
        if team_members is not UNSET:
            field_dict["team_members"] = team_members

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        type_ = NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0Type(d.pop("type"))

        _team_members = d.pop("team_members", UNSET)
        team_members: Union[Unset, NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0TeamMembers]
        if isinstance(_team_members, Unset):
            team_members = UNSET
        else:
            team_members = NewEscalationPolicyLevelDataAttributesNotificationTargetParamsItemType0TeamMembers(
                _team_members
            )

        new_escalation_policy_level_data_attributes_notification_target_params_item_type_0 = cls(
            id=id,
            type_=type_,
            team_members=team_members,
        )

        new_escalation_policy_level_data_attributes_notification_target_params_item_type_0.additional_properties = d
        return new_escalation_policy_level_data_attributes_notification_target_params_item_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
