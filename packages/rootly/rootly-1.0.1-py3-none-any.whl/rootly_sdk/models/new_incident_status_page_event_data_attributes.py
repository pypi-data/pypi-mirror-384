from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_incident_status_page_event_data_attributes_status import (
    NewIncidentStatusPageEventDataAttributesStatus,
    check_new_incident_status_page_event_data_attributes_status,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewIncidentStatusPageEventDataAttributes")


@_attrs_define
class NewIncidentStatusPageEventDataAttributes:
    """
    Attributes:
        event (str): The summary of the incident event
        status_page_id (Union[Unset, str]): Unique ID of the status page you wish to post the event to
        status (Union[Unset, NewIncidentStatusPageEventDataAttributesStatus]): The status of the incident event
        notify_subscribers (Union[None, Unset, bool]): Notify all status pages subscribers Default: False.
        should_tweet (Union[None, Unset, bool]): For Statuspage.io integrated pages auto publishes a tweet for your
            update Default: False.
    """

    event: str
    status_page_id: Union[Unset, str] = UNSET
    status: Union[Unset, NewIncidentStatusPageEventDataAttributesStatus] = UNSET
    notify_subscribers: Union[None, Unset, bool] = False
    should_tweet: Union[None, Unset, bool] = False

    def to_dict(self) -> dict[str, Any]:
        event = self.event

        status_page_id = self.status_page_id

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status

        notify_subscribers: Union[None, Unset, bool]
        if isinstance(self.notify_subscribers, Unset):
            notify_subscribers = UNSET
        else:
            notify_subscribers = self.notify_subscribers

        should_tweet: Union[None, Unset, bool]
        if isinstance(self.should_tweet, Unset):
            should_tweet = UNSET
        else:
            should_tweet = self.should_tweet

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "event": event,
            }
        )
        if status_page_id is not UNSET:
            field_dict["status_page_id"] = status_page_id
        if status is not UNSET:
            field_dict["status"] = status
        if notify_subscribers is not UNSET:
            field_dict["notify_subscribers"] = notify_subscribers
        if should_tweet is not UNSET:
            field_dict["should_tweet"] = should_tweet

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        event = d.pop("event")

        status_page_id = d.pop("status_page_id", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, NewIncidentStatusPageEventDataAttributesStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = check_new_incident_status_page_event_data_attributes_status(_status)

        def _parse_notify_subscribers(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        notify_subscribers = _parse_notify_subscribers(d.pop("notify_subscribers", UNSET))

        def _parse_should_tweet(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        should_tweet = _parse_should_tweet(d.pop("should_tweet", UNSET))

        new_incident_status_page_event_data_attributes = cls(
            event=event,
            status_page_id=status_page_id,
            status=status,
            notify_subscribers=notify_subscribers,
            should_tweet=should_tweet,
        )

        return new_incident_status_page_event_data_attributes
