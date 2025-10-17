from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.heartbeat_interval_unit import HeartbeatIntervalUnit
from ..models.heartbeat_notification_target_type import HeartbeatNotificationTargetType
from ..models.heartbeat_status import HeartbeatStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="Heartbeat")


@_attrs_define
class Heartbeat:
    """
    Attributes:
        name (str): The name of the heartbeat
        alert_summary (str): Summary of alerts triggered when heartbeat expires.
        interval (int):
        interval_unit (HeartbeatIntervalUnit):
        notification_target_id (str):
        notification_target_type (HeartbeatNotificationTargetType):
        enabled (bool): Whether to trigger alerts when heartbeat is expired.
        status (HeartbeatStatus):
        created_at (str): Date of creation
        updated_at (str): Date of last update
        description (Union[None, Unset, str]): The description of the heartbeat
        alert_urgency_id (Union[None, Unset, str]): Urgency of alerts triggered when heartbeat expires.
        ping_url (Union[None, Unset, str]): URL to receive heartbeat pings.
        secret (Union[None, Unset, str]): Secret used as bearer token when pinging heartbeat.
        last_pinged_at (Union[None, Unset, str]): When the heartbeat was last pinged.
        expires_at (Union[None, Unset, str]): When heartbeat expires
    """

    name: str
    alert_summary: str
    interval: int
    interval_unit: HeartbeatIntervalUnit
    notification_target_id: str
    notification_target_type: HeartbeatNotificationTargetType
    enabled: bool
    status: HeartbeatStatus
    created_at: str
    updated_at: str
    description: Union[None, Unset, str] = UNSET
    alert_urgency_id: Union[None, Unset, str] = UNSET
    ping_url: Union[None, Unset, str] = UNSET
    secret: Union[None, Unset, str] = UNSET
    last_pinged_at: Union[None, Unset, str] = UNSET
    expires_at: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        alert_summary = self.alert_summary

        interval = self.interval

        interval_unit = self.interval_unit.value

        notification_target_id = self.notification_target_id

        notification_target_type = self.notification_target_type.value

        enabled = self.enabled

        status = self.status.value

        created_at = self.created_at

        updated_at = self.updated_at

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        alert_urgency_id: Union[None, Unset, str]
        if isinstance(self.alert_urgency_id, Unset):
            alert_urgency_id = UNSET
        else:
            alert_urgency_id = self.alert_urgency_id

        ping_url: Union[None, Unset, str]
        if isinstance(self.ping_url, Unset):
            ping_url = UNSET
        else:
            ping_url = self.ping_url

        secret: Union[None, Unset, str]
        if isinstance(self.secret, Unset):
            secret = UNSET
        else:
            secret = self.secret

        last_pinged_at: Union[None, Unset, str]
        if isinstance(self.last_pinged_at, Unset):
            last_pinged_at = UNSET
        else:
            last_pinged_at = self.last_pinged_at

        expires_at: Union[None, Unset, str]
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = self.expires_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "alert_summary": alert_summary,
                "interval": interval,
                "interval_unit": interval_unit,
                "notification_target_id": notification_target_id,
                "notification_target_type": notification_target_type,
                "enabled": enabled,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if alert_urgency_id is not UNSET:
            field_dict["alert_urgency_id"] = alert_urgency_id
        if ping_url is not UNSET:
            field_dict["ping_url"] = ping_url
        if secret is not UNSET:
            field_dict["secret"] = secret
        if last_pinged_at is not UNSET:
            field_dict["last_pinged_at"] = last_pinged_at
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        alert_summary = d.pop("alert_summary")

        interval = d.pop("interval")

        interval_unit = HeartbeatIntervalUnit(d.pop("interval_unit"))

        notification_target_id = d.pop("notification_target_id")

        notification_target_type = HeartbeatNotificationTargetType(d.pop("notification_target_type"))

        enabled = d.pop("enabled")

        status = HeartbeatStatus(d.pop("status"))

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_alert_urgency_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        alert_urgency_id = _parse_alert_urgency_id(d.pop("alert_urgency_id", UNSET))

        def _parse_ping_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ping_url = _parse_ping_url(d.pop("ping_url", UNSET))

        def _parse_secret(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        secret = _parse_secret(d.pop("secret", UNSET))

        def _parse_last_pinged_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        last_pinged_at = _parse_last_pinged_at(d.pop("last_pinged_at", UNSET))

        def _parse_expires_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        heartbeat = cls(
            name=name,
            alert_summary=alert_summary,
            interval=interval,
            interval_unit=interval_unit,
            notification_target_id=notification_target_id,
            notification_target_type=notification_target_type,
            enabled=enabled,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            alert_urgency_id=alert_urgency_id,
            ping_url=ping_url,
            secret=secret,
            last_pinged_at=last_pinged_at,
            expires_at=expires_at,
        )

        heartbeat.additional_properties = d
        return heartbeat

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
