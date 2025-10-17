import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.new_pulse_data_attributes_data_type_0 import NewPulseDataAttributesDataType0
    from ..models.new_pulse_data_attributes_labels_item_type_0 import NewPulseDataAttributesLabelsItemType0
    from ..models.new_pulse_data_attributes_refs_item_type_0 import NewPulseDataAttributesRefsItemType0


T = TypeVar("T", bound="NewPulseDataAttributes")


@_attrs_define
class NewPulseDataAttributes:
    """
    Attributes:
        summary (str): The summary of the pulse
        source (Union[None, Unset, str]): The source of the pulse (eg: k8s)
        service_ids (Union[None, Unset, list[str]]): The Service ID's to attach to the pulse
        environment_ids (Union[None, Unset, list[str]]): The Environment ID's to attach to the pulse
        started_at (Union[None, Unset, datetime.datetime]): Pulse start datetime
        ended_at (Union[None, Unset, datetime.datetime]): Pulse end datetime
        external_url (Union[None, Unset, str]): The external url of the pulse
        labels (Union[Unset, list[Union['NewPulseDataAttributesLabelsItemType0', None]]]):
        refs (Union[Unset, list[Union['NewPulseDataAttributesRefsItemType0', None]]]):
        data (Union['NewPulseDataAttributesDataType0', None, Unset]): Additional data
    """

    summary: str
    source: Union[None, Unset, str] = UNSET
    service_ids: Union[None, Unset, list[str]] = UNSET
    environment_ids: Union[None, Unset, list[str]] = UNSET
    started_at: Union[None, Unset, datetime.datetime] = UNSET
    ended_at: Union[None, Unset, datetime.datetime] = UNSET
    external_url: Union[None, Unset, str] = UNSET
    labels: Union[Unset, list[Union["NewPulseDataAttributesLabelsItemType0", None]]] = UNSET
    refs: Union[Unset, list[Union["NewPulseDataAttributesRefsItemType0", None]]] = UNSET
    data: Union["NewPulseDataAttributesDataType0", None, Unset] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.new_pulse_data_attributes_data_type_0 import NewPulseDataAttributesDataType0
        from ..models.new_pulse_data_attributes_labels_item_type_0 import NewPulseDataAttributesLabelsItemType0
        from ..models.new_pulse_data_attributes_refs_item_type_0 import NewPulseDataAttributesRefsItemType0

        summary = self.summary

        source: Union[None, Unset, str]
        if isinstance(self.source, Unset):
            source = UNSET
        else:
            source = self.source

        service_ids: Union[None, Unset, list[str]]
        if isinstance(self.service_ids, Unset):
            service_ids = UNSET
        elif isinstance(self.service_ids, list):
            service_ids = self.service_ids

        else:
            service_ids = self.service_ids

        environment_ids: Union[None, Unset, list[str]]
        if isinstance(self.environment_ids, Unset):
            environment_ids = UNSET
        elif isinstance(self.environment_ids, list):
            environment_ids = self.environment_ids

        else:
            environment_ids = self.environment_ids

        started_at: Union[None, Unset, str]
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        ended_at: Union[None, Unset, str]
        if isinstance(self.ended_at, Unset):
            ended_at = UNSET
        elif isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        external_url: Union[None, Unset, str]
        if isinstance(self.external_url, Unset):
            external_url = UNSET
        else:
            external_url = self.external_url

        labels: Union[Unset, list[Union[None, dict[str, Any]]]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = []
            for labels_item_data in self.labels:
                labels_item: Union[None, dict[str, Any]]
                if isinstance(labels_item_data, NewPulseDataAttributesLabelsItemType0):
                    labels_item = labels_item_data.to_dict()
                else:
                    labels_item = labels_item_data
                labels.append(labels_item)

        refs: Union[Unset, list[Union[None, dict[str, Any]]]] = UNSET
        if not isinstance(self.refs, Unset):
            refs = []
            for refs_item_data in self.refs:
                refs_item: Union[None, dict[str, Any]]
                if isinstance(refs_item_data, NewPulseDataAttributesRefsItemType0):
                    refs_item = refs_item_data.to_dict()
                else:
                    refs_item = refs_item_data
                refs.append(refs_item)

        data: Union[None, Unset, dict[str, Any]]
        if isinstance(self.data, Unset):
            data = UNSET
        elif isinstance(self.data, NewPulseDataAttributesDataType0):
            data = self.data.to_dict()
        else:
            data = self.data

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "summary": summary,
            }
        )
        if source is not UNSET:
            field_dict["source"] = source
        if service_ids is not UNSET:
            field_dict["service_ids"] = service_ids
        if environment_ids is not UNSET:
            field_dict["environment_ids"] = environment_ids
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if external_url is not UNSET:
            field_dict["external_url"] = external_url
        if labels is not UNSET:
            field_dict["labels"] = labels
        if refs is not UNSET:
            field_dict["refs"] = refs
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.new_pulse_data_attributes_data_type_0 import NewPulseDataAttributesDataType0
        from ..models.new_pulse_data_attributes_labels_item_type_0 import NewPulseDataAttributesLabelsItemType0
        from ..models.new_pulse_data_attributes_refs_item_type_0 import NewPulseDataAttributesRefsItemType0

        d = dict(src_dict)
        summary = d.pop("summary")

        def _parse_source(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        source = _parse_source(d.pop("source", UNSET))

        def _parse_service_ids(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                service_ids_type_0 = cast(list[str], data)

                return service_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        service_ids = _parse_service_ids(d.pop("service_ids", UNSET))

        def _parse_environment_ids(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                environment_ids_type_0 = cast(list[str], data)

                return environment_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        environment_ids = _parse_environment_ids(d.pop("environment_ids", UNSET))

        def _parse_started_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_ended_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = isoparse(data)

                return ended_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        ended_at = _parse_ended_at(d.pop("ended_at", UNSET))

        def _parse_external_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_url = _parse_external_url(d.pop("external_url", UNSET))

        labels = []
        _labels = d.pop("labels", UNSET)
        for labels_item_data in _labels or []:

            def _parse_labels_item(data: object) -> Union["NewPulseDataAttributesLabelsItemType0", None]:
                if data is None:
                    return data
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    labels_item_type_0 = NewPulseDataAttributesLabelsItemType0.from_dict(data)

                    return labels_item_type_0
                except:  # noqa: E722
                    pass
                return cast(Union["NewPulseDataAttributesLabelsItemType0", None], data)

            labels_item = _parse_labels_item(labels_item_data)

            labels.append(labels_item)

        refs = []
        _refs = d.pop("refs", UNSET)
        for refs_item_data in _refs or []:

            def _parse_refs_item(data: object) -> Union["NewPulseDataAttributesRefsItemType0", None]:
                if data is None:
                    return data
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    refs_item_type_0 = NewPulseDataAttributesRefsItemType0.from_dict(data)

                    return refs_item_type_0
                except:  # noqa: E722
                    pass
                return cast(Union["NewPulseDataAttributesRefsItemType0", None], data)

            refs_item = _parse_refs_item(refs_item_data)

            refs.append(refs_item)

        def _parse_data(data: object) -> Union["NewPulseDataAttributesDataType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_0 = NewPulseDataAttributesDataType0.from_dict(data)

                return data_type_0
            except:  # noqa: E722
                pass
            return cast(Union["NewPulseDataAttributesDataType0", None, Unset], data)

        data = _parse_data(d.pop("data", UNSET))

        new_pulse_data_attributes = cls(
            summary=summary,
            source=source,
            service_ids=service_ids,
            environment_ids=environment_ids,
            started_at=started_at,
            ended_at=ended_at,
            external_url=external_url,
            labels=labels,
            refs=refs,
            data=data,
        )

        return new_pulse_data_attributes
