from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_notification_rule_enabled_contact_types_item import UserNotificationRuleEnabledContactTypesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserNotificationRule")


@_attrs_define
class UserNotificationRule:
    """
    Attributes:
        user_id (Union[Unset, int]):
        delay (Union[None, Unset, int]): Delay after which rule gets triggered
        position (Union[None, Unset, int]): Position of the rule
        user_email_address_id (Union[None, Unset, str]): User email address to which notification to be sent
        user_call_number_id (Union[None, Unset, str]): User phone number to which notification to be sent
        user_sms_number_id (Union[None, Unset, str]): User sms number to which notification to be sent
        user_device_id (Union[None, Unset, str]): User device to which notification to be sent
        enabled_contact_types (Union[Unset, list[UserNotificationRuleEnabledContactTypesItem]]): Contact types for which
            notification needs to be enabled
        created_at (Union[Unset, str]): Date of creation
        updated_at (Union[Unset, str]): Date of last update
    """

    user_id: Union[Unset, int] = UNSET
    delay: Union[None, Unset, int] = UNSET
    position: Union[None, Unset, int] = UNSET
    user_email_address_id: Union[None, Unset, str] = UNSET
    user_call_number_id: Union[None, Unset, str] = UNSET
    user_sms_number_id: Union[None, Unset, str] = UNSET
    user_device_id: Union[None, Unset, str] = UNSET
    enabled_contact_types: Union[Unset, list[UserNotificationRuleEnabledContactTypesItem]] = UNSET
    created_at: Union[Unset, str] = UNSET
    updated_at: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        delay: Union[None, Unset, int]
        if isinstance(self.delay, Unset):
            delay = UNSET
        else:
            delay = self.delay

        position: Union[None, Unset, int]
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        user_email_address_id: Union[None, Unset, str]
        if isinstance(self.user_email_address_id, Unset):
            user_email_address_id = UNSET
        else:
            user_email_address_id = self.user_email_address_id

        user_call_number_id: Union[None, Unset, str]
        if isinstance(self.user_call_number_id, Unset):
            user_call_number_id = UNSET
        else:
            user_call_number_id = self.user_call_number_id

        user_sms_number_id: Union[None, Unset, str]
        if isinstance(self.user_sms_number_id, Unset):
            user_sms_number_id = UNSET
        else:
            user_sms_number_id = self.user_sms_number_id

        user_device_id: Union[None, Unset, str]
        if isinstance(self.user_device_id, Unset):
            user_device_id = UNSET
        else:
            user_device_id = self.user_device_id

        enabled_contact_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.enabled_contact_types, Unset):
            enabled_contact_types = []
            for enabled_contact_types_item_data in self.enabled_contact_types:
                enabled_contact_types_item = enabled_contact_types_item_data.value
                enabled_contact_types.append(enabled_contact_types_item)

        created_at = self.created_at

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if delay is not UNSET:
            field_dict["delay"] = delay
        if position is not UNSET:
            field_dict["position"] = position
        if user_email_address_id is not UNSET:
            field_dict["user_email_address_id"] = user_email_address_id
        if user_call_number_id is not UNSET:
            field_dict["user_call_number_id"] = user_call_number_id
        if user_sms_number_id is not UNSET:
            field_dict["user_sms_number_id"] = user_sms_number_id
        if user_device_id is not UNSET:
            field_dict["user_device_id"] = user_device_id
        if enabled_contact_types is not UNSET:
            field_dict["enabled_contact_types"] = enabled_contact_types
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id", UNSET)

        def _parse_delay(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        delay = _parse_delay(d.pop("delay", UNSET))

        def _parse_position(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        position = _parse_position(d.pop("position", UNSET))

        def _parse_user_email_address_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_email_address_id = _parse_user_email_address_id(d.pop("user_email_address_id", UNSET))

        def _parse_user_call_number_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_call_number_id = _parse_user_call_number_id(d.pop("user_call_number_id", UNSET))

        def _parse_user_sms_number_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_sms_number_id = _parse_user_sms_number_id(d.pop("user_sms_number_id", UNSET))

        def _parse_user_device_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_device_id = _parse_user_device_id(d.pop("user_device_id", UNSET))

        enabled_contact_types = []
        _enabled_contact_types = d.pop("enabled_contact_types", UNSET)
        for enabled_contact_types_item_data in _enabled_contact_types or []:
            enabled_contact_types_item = UserNotificationRuleEnabledContactTypesItem(enabled_contact_types_item_data)

            enabled_contact_types.append(enabled_contact_types_item)

        created_at = d.pop("created_at", UNSET)

        updated_at = d.pop("updated_at", UNSET)

        user_notification_rule = cls(
            user_id=user_id,
            delay=delay,
            position=position,
            user_email_address_id=user_email_address_id,
            user_call_number_id=user_call_number_id,
            user_sms_number_id=user_sms_number_id,
            user_device_id=user_device_id,
            enabled_contact_types=enabled_contact_types,
            created_at=created_at,
            updated_at=updated_at,
        )

        user_notification_rule.additional_properties = d
        return user_notification_rule

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
