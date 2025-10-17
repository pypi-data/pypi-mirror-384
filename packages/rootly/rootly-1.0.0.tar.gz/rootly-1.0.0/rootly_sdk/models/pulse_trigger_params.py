from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.pulse_trigger_params_pulse_condition import PulseTriggerParamsPulseCondition
from ..models.pulse_trigger_params_pulse_condition_label import PulseTriggerParamsPulseConditionLabel
from ..models.pulse_trigger_params_pulse_condition_payload import PulseTriggerParamsPulseConditionPayload
from ..models.pulse_trigger_params_pulse_condition_source import PulseTriggerParamsPulseConditionSource
from ..models.pulse_trigger_params_trigger_type import PulseTriggerParamsTriggerType
from ..models.pulse_trigger_params_triggers_item import PulseTriggerParamsTriggersItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="PulseTriggerParams")


@_attrs_define
class PulseTriggerParams:
    """
    Attributes:
        trigger_type (PulseTriggerParamsTriggerType):
        triggers (Union[Unset, list[PulseTriggerParamsTriggersItem]]):
        pulse_condition (Union[Unset, PulseTriggerParamsPulseCondition]):
        pulse_condition_source (Union[Unset, PulseTriggerParamsPulseConditionSource]):  Default:
            PulseTriggerParamsPulseConditionSource.ANY.
        pulse_condition_source_use_regexp (Union[Unset, bool]):  Default: False.
        pulse_sources (Union[Unset, list[str]]):
        pulse_condition_label (Union[Unset, PulseTriggerParamsPulseConditionLabel]):  Default:
            PulseTriggerParamsPulseConditionLabel.ANY.
        pulse_condition_label_use_regexp (Union[Unset, bool]):  Default: False.
        pulse_labels (Union[Unset, list[str]]):
        pulse_condition_payload (Union[Unset, PulseTriggerParamsPulseConditionPayload]):  Default:
            PulseTriggerParamsPulseConditionPayload.ANY.
        pulse_condition_payload_use_regexp (Union[Unset, bool]):  Default: False.
        pulse_payload (Union[Unset, list[str]]):
        pulse_query_payload (Union[None, Unset, str]): You can use jsonpath syntax. eg: $.incident.teams[*]
    """

    trigger_type: PulseTriggerParamsTriggerType
    triggers: Union[Unset, list[PulseTriggerParamsTriggersItem]] = UNSET
    pulse_condition: Union[Unset, PulseTriggerParamsPulseCondition] = UNSET
    pulse_condition_source: Union[Unset, PulseTriggerParamsPulseConditionSource] = (
        PulseTriggerParamsPulseConditionSource.ANY
    )
    pulse_condition_source_use_regexp: Union[Unset, bool] = False
    pulse_sources: Union[Unset, list[str]] = UNSET
    pulse_condition_label: Union[Unset, PulseTriggerParamsPulseConditionLabel] = (
        PulseTriggerParamsPulseConditionLabel.ANY
    )
    pulse_condition_label_use_regexp: Union[Unset, bool] = False
    pulse_labels: Union[Unset, list[str]] = UNSET
    pulse_condition_payload: Union[Unset, PulseTriggerParamsPulseConditionPayload] = (
        PulseTriggerParamsPulseConditionPayload.ANY
    )
    pulse_condition_payload_use_regexp: Union[Unset, bool] = False
    pulse_payload: Union[Unset, list[str]] = UNSET
    pulse_query_payload: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        trigger_type = self.trigger_type.value

        triggers: Union[Unset, list[str]] = UNSET
        if not isinstance(self.triggers, Unset):
            triggers = []
            for triggers_item_data in self.triggers:
                triggers_item = triggers_item_data.value
                triggers.append(triggers_item)

        pulse_condition: Union[Unset, str] = UNSET
        if not isinstance(self.pulse_condition, Unset):
            pulse_condition = self.pulse_condition.value

        pulse_condition_source: Union[Unset, str] = UNSET
        if not isinstance(self.pulse_condition_source, Unset):
            pulse_condition_source = self.pulse_condition_source.value

        pulse_condition_source_use_regexp = self.pulse_condition_source_use_regexp

        pulse_sources: Union[Unset, list[str]] = UNSET
        if not isinstance(self.pulse_sources, Unset):
            pulse_sources = self.pulse_sources

        pulse_condition_label: Union[Unset, str] = UNSET
        if not isinstance(self.pulse_condition_label, Unset):
            pulse_condition_label = self.pulse_condition_label.value

        pulse_condition_label_use_regexp = self.pulse_condition_label_use_regexp

        pulse_labels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.pulse_labels, Unset):
            pulse_labels = self.pulse_labels

        pulse_condition_payload: Union[Unset, str] = UNSET
        if not isinstance(self.pulse_condition_payload, Unset):
            pulse_condition_payload = self.pulse_condition_payload.value

        pulse_condition_payload_use_regexp = self.pulse_condition_payload_use_regexp

        pulse_payload: Union[Unset, list[str]] = UNSET
        if not isinstance(self.pulse_payload, Unset):
            pulse_payload = self.pulse_payload

        pulse_query_payload: Union[None, Unset, str]
        if isinstance(self.pulse_query_payload, Unset):
            pulse_query_payload = UNSET
        else:
            pulse_query_payload = self.pulse_query_payload

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trigger_type": trigger_type,
            }
        )
        if triggers is not UNSET:
            field_dict["triggers"] = triggers
        if pulse_condition is not UNSET:
            field_dict["pulse_condition"] = pulse_condition
        if pulse_condition_source is not UNSET:
            field_dict["pulse_condition_source"] = pulse_condition_source
        if pulse_condition_source_use_regexp is not UNSET:
            field_dict["pulse_condition_source_use_regexp"] = pulse_condition_source_use_regexp
        if pulse_sources is not UNSET:
            field_dict["pulse_sources"] = pulse_sources
        if pulse_condition_label is not UNSET:
            field_dict["pulse_condition_label"] = pulse_condition_label
        if pulse_condition_label_use_regexp is not UNSET:
            field_dict["pulse_condition_label_use_regexp"] = pulse_condition_label_use_regexp
        if pulse_labels is not UNSET:
            field_dict["pulse_labels"] = pulse_labels
        if pulse_condition_payload is not UNSET:
            field_dict["pulse_condition_payload"] = pulse_condition_payload
        if pulse_condition_payload_use_regexp is not UNSET:
            field_dict["pulse_condition_payload_use_regexp"] = pulse_condition_payload_use_regexp
        if pulse_payload is not UNSET:
            field_dict["pulse_payload"] = pulse_payload
        if pulse_query_payload is not UNSET:
            field_dict["pulse_query_payload"] = pulse_query_payload

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        trigger_type = PulseTriggerParamsTriggerType(d.pop("trigger_type"))

        triggers = []
        _triggers = d.pop("triggers", UNSET)
        for triggers_item_data in _triggers or []:
            triggers_item = PulseTriggerParamsTriggersItem(triggers_item_data)

            triggers.append(triggers_item)

        _pulse_condition = d.pop("pulse_condition", UNSET)
        pulse_condition: Union[Unset, PulseTriggerParamsPulseCondition]
        if isinstance(_pulse_condition, Unset):
            pulse_condition = UNSET
        else:
            pulse_condition = PulseTriggerParamsPulseCondition(_pulse_condition)

        _pulse_condition_source = d.pop("pulse_condition_source", UNSET)
        pulse_condition_source: Union[Unset, PulseTriggerParamsPulseConditionSource]
        if isinstance(_pulse_condition_source, Unset):
            pulse_condition_source = UNSET
        else:
            pulse_condition_source = PulseTriggerParamsPulseConditionSource(_pulse_condition_source)

        pulse_condition_source_use_regexp = d.pop("pulse_condition_source_use_regexp", UNSET)

        pulse_sources = cast(list[str], d.pop("pulse_sources", UNSET))

        _pulse_condition_label = d.pop("pulse_condition_label", UNSET)
        pulse_condition_label: Union[Unset, PulseTriggerParamsPulseConditionLabel]
        if isinstance(_pulse_condition_label, Unset):
            pulse_condition_label = UNSET
        else:
            pulse_condition_label = PulseTriggerParamsPulseConditionLabel(_pulse_condition_label)

        pulse_condition_label_use_regexp = d.pop("pulse_condition_label_use_regexp", UNSET)

        pulse_labels = cast(list[str], d.pop("pulse_labels", UNSET))

        _pulse_condition_payload = d.pop("pulse_condition_payload", UNSET)
        pulse_condition_payload: Union[Unset, PulseTriggerParamsPulseConditionPayload]
        if isinstance(_pulse_condition_payload, Unset):
            pulse_condition_payload = UNSET
        else:
            pulse_condition_payload = PulseTriggerParamsPulseConditionPayload(_pulse_condition_payload)

        pulse_condition_payload_use_regexp = d.pop("pulse_condition_payload_use_regexp", UNSET)

        pulse_payload = cast(list[str], d.pop("pulse_payload", UNSET))

        def _parse_pulse_query_payload(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        pulse_query_payload = _parse_pulse_query_payload(d.pop("pulse_query_payload", UNSET))

        pulse_trigger_params = cls(
            trigger_type=trigger_type,
            triggers=triggers,
            pulse_condition=pulse_condition,
            pulse_condition_source=pulse_condition_source,
            pulse_condition_source_use_regexp=pulse_condition_source_use_regexp,
            pulse_sources=pulse_sources,
            pulse_condition_label=pulse_condition_label,
            pulse_condition_label_use_regexp=pulse_condition_label_use_regexp,
            pulse_labels=pulse_labels,
            pulse_condition_payload=pulse_condition_payload,
            pulse_condition_payload_use_regexp=pulse_condition_payload_use_regexp,
            pulse_payload=pulse_payload,
            pulse_query_payload=pulse_query_payload,
        )

        pulse_trigger_params.additional_properties = d
        return pulse_trigger_params

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
