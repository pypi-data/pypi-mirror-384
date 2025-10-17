from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.change_slack_channel_privacy_task_params_privacy import (
    ChangeSlackChannelPrivacyTaskParamsPrivacy,
    check_change_slack_channel_privacy_task_params_privacy,
)
from ..models.change_slack_channel_privacy_task_params_task_type import (
    ChangeSlackChannelPrivacyTaskParamsTaskType,
    check_change_slack_channel_privacy_task_params_task_type,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.change_slack_channel_privacy_task_params_channel import ChangeSlackChannelPrivacyTaskParamsChannel


T = TypeVar("T", bound="ChangeSlackChannelPrivacyTaskParams")


@_attrs_define
class ChangeSlackChannelPrivacyTaskParams:
    """
    Attributes:
        privacy (ChangeSlackChannelPrivacyTaskParamsPrivacy):
        task_type (Union[Unset, ChangeSlackChannelPrivacyTaskParamsTaskType]):
        channel (Union[Unset, ChangeSlackChannelPrivacyTaskParamsChannel]):
    """

    privacy: ChangeSlackChannelPrivacyTaskParamsPrivacy
    task_type: Union[Unset, ChangeSlackChannelPrivacyTaskParamsTaskType] = UNSET
    channel: Union[Unset, "ChangeSlackChannelPrivacyTaskParamsChannel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        privacy: str = self.privacy

        task_type: Union[Unset, str] = UNSET
        if not isinstance(self.task_type, Unset):
            task_type = self.task_type

        channel: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.channel, Unset):
            channel = self.channel.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "privacy": privacy,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type
        if channel is not UNSET:
            field_dict["channel"] = channel

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.change_slack_channel_privacy_task_params_channel import ChangeSlackChannelPrivacyTaskParamsChannel

        d = dict(src_dict)
        privacy = check_change_slack_channel_privacy_task_params_privacy(d.pop("privacy"))

        _task_type = d.pop("task_type", UNSET)
        task_type: Union[Unset, ChangeSlackChannelPrivacyTaskParamsTaskType]
        if isinstance(_task_type, Unset):
            task_type = UNSET
        else:
            task_type = check_change_slack_channel_privacy_task_params_task_type(_task_type)

        _channel = d.pop("channel", UNSET)
        channel: Union[Unset, ChangeSlackChannelPrivacyTaskParamsChannel]
        if isinstance(_channel, Unset):
            channel = UNSET
        else:
            channel = ChangeSlackChannelPrivacyTaskParamsChannel.from_dict(_channel)

        change_slack_channel_privacy_task_params = cls(
            privacy=privacy,
            task_type=task_type,
            channel=channel,
        )

        change_slack_channel_privacy_task_params.additional_properties = d
        return change_slack_channel_privacy_task_params

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
