from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.live_call_router_country_code import LiveCallRouterCountryCode
from ..models.live_call_router_kind import LiveCallRouterKind
from ..models.live_call_router_phone_type import LiveCallRouterPhoneType
from ..models.live_call_router_waiting_music_url import LiveCallRouterWaitingMusicUrl
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.live_call_router_escalation_policy_trigger_params import LiveCallRouterEscalationPolicyTriggerParams
    from ..models.live_call_router_paging_targets_item import LiveCallRouterPagingTargetsItem


T = TypeVar("T", bound="LiveCallRouter")


@_attrs_define
class LiveCallRouter:
    """
    Attributes:
        name (str): The name of the live_call_router
        created_at (str): Date of creation
        updated_at (str): Date of last update
        kind (Union[Unset, LiveCallRouterKind]): The kind of the live_call_router
        enabled (Union[Unset, bool]): Whether the live_call_router is enabled
        country_code (Union[Unset, LiveCallRouterCountryCode]): The country code of the live_call_router
        phone_type (Union[Unset, LiveCallRouterPhoneType]): The phone type of the live_call_router
        phone_number (Union[Unset, str]): You can select a phone number using
            [generate_phone_number](#//api/v1/live_call_routers/generate_phone_number) API and pass that phone number here
            to register
        voicemail_greeting (Union[Unset, str]): The voicemail greeting of the live_call_router
        caller_greeting (Union[Unset, str]): The caller greeting message of the live_call_router
        waiting_music_url (Union[Unset, LiveCallRouterWaitingMusicUrl]): The waiting music URL of the live_call_router
        sent_to_voicemail_delay (Union[Unset, int]): The delay (seconds) after which the caller in redirected to
            voicemail
        should_redirect_to_voicemail_on_no_answer (Union[Unset, bool]): This prompts the caller to choose voicemail or
            connect live
        escalation_level_delay_in_seconds (Union[Unset, int]): This overrides the delay (seconds) in escalation levels
        should_auto_resolve_alert_on_call_end (Union[Unset, bool]): This overrides the delay (seconds) in escalation
            levels
        alert_urgency_id (Union[Unset, str]): This is used in escalation paths to determine who to page
        calling_tree_prompt (Union[Unset, str]): The audio instructions callers will hear when they call this number,
            prompting them to select from available options to route their call
        paging_targets (Union[Unset, list['LiveCallRouterPagingTargetsItem']]): Paging targets that callers can select
            from when this live call router is configured as a phone tree.
        escalation_policy_trigger_params (Union[Unset, LiveCallRouterEscalationPolicyTriggerParams]):
    """

    name: str
    created_at: str
    updated_at: str
    kind: Union[Unset, LiveCallRouterKind] = UNSET
    enabled: Union[Unset, bool] = UNSET
    country_code: Union[Unset, LiveCallRouterCountryCode] = UNSET
    phone_type: Union[Unset, LiveCallRouterPhoneType] = UNSET
    phone_number: Union[Unset, str] = UNSET
    voicemail_greeting: Union[Unset, str] = UNSET
    caller_greeting: Union[Unset, str] = UNSET
    waiting_music_url: Union[Unset, LiveCallRouterWaitingMusicUrl] = UNSET
    sent_to_voicemail_delay: Union[Unset, int] = UNSET
    should_redirect_to_voicemail_on_no_answer: Union[Unset, bool] = UNSET
    escalation_level_delay_in_seconds: Union[Unset, int] = UNSET
    should_auto_resolve_alert_on_call_end: Union[Unset, bool] = UNSET
    alert_urgency_id: Union[Unset, str] = UNSET
    calling_tree_prompt: Union[Unset, str] = UNSET
    paging_targets: Union[Unset, list["LiveCallRouterPagingTargetsItem"]] = UNSET
    escalation_policy_trigger_params: Union[Unset, "LiveCallRouterEscalationPolicyTriggerParams"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        created_at = self.created_at

        updated_at = self.updated_at

        kind: Union[Unset, str] = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        enabled = self.enabled

        country_code: Union[Unset, str] = UNSET
        if not isinstance(self.country_code, Unset):
            country_code = self.country_code.value

        phone_type: Union[Unset, str] = UNSET
        if not isinstance(self.phone_type, Unset):
            phone_type = self.phone_type.value

        phone_number = self.phone_number

        voicemail_greeting = self.voicemail_greeting

        caller_greeting = self.caller_greeting

        waiting_music_url: Union[Unset, str] = UNSET
        if not isinstance(self.waiting_music_url, Unset):
            waiting_music_url = self.waiting_music_url.value

        sent_to_voicemail_delay = self.sent_to_voicemail_delay

        should_redirect_to_voicemail_on_no_answer = self.should_redirect_to_voicemail_on_no_answer

        escalation_level_delay_in_seconds = self.escalation_level_delay_in_seconds

        should_auto_resolve_alert_on_call_end = self.should_auto_resolve_alert_on_call_end

        alert_urgency_id = self.alert_urgency_id

        calling_tree_prompt = self.calling_tree_prompt

        paging_targets: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.paging_targets, Unset):
            paging_targets = []
            for paging_targets_item_data in self.paging_targets:
                paging_targets_item = paging_targets_item_data.to_dict()
                paging_targets.append(paging_targets_item)

        escalation_policy_trigger_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.escalation_policy_trigger_params, Unset):
            escalation_policy_trigger_params = self.escalation_policy_trigger_params.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if kind is not UNSET:
            field_dict["kind"] = kind
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if country_code is not UNSET:
            field_dict["country_code"] = country_code
        if phone_type is not UNSET:
            field_dict["phone_type"] = phone_type
        if phone_number is not UNSET:
            field_dict["phone_number"] = phone_number
        if voicemail_greeting is not UNSET:
            field_dict["voicemail_greeting"] = voicemail_greeting
        if caller_greeting is not UNSET:
            field_dict["caller_greeting"] = caller_greeting
        if waiting_music_url is not UNSET:
            field_dict["waiting_music_url"] = waiting_music_url
        if sent_to_voicemail_delay is not UNSET:
            field_dict["sent_to_voicemail_delay"] = sent_to_voicemail_delay
        if should_redirect_to_voicemail_on_no_answer is not UNSET:
            field_dict["should_redirect_to_voicemail_on_no_answer"] = should_redirect_to_voicemail_on_no_answer
        if escalation_level_delay_in_seconds is not UNSET:
            field_dict["escalation_level_delay_in_seconds"] = escalation_level_delay_in_seconds
        if should_auto_resolve_alert_on_call_end is not UNSET:
            field_dict["should_auto_resolve_alert_on_call_end"] = should_auto_resolve_alert_on_call_end
        if alert_urgency_id is not UNSET:
            field_dict["alert_urgency_id"] = alert_urgency_id
        if calling_tree_prompt is not UNSET:
            field_dict["calling_tree_prompt"] = calling_tree_prompt
        if paging_targets is not UNSET:
            field_dict["paging_targets"] = paging_targets
        if escalation_policy_trigger_params is not UNSET:
            field_dict["escalation_policy_trigger_params"] = escalation_policy_trigger_params

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.live_call_router_escalation_policy_trigger_params import (
            LiveCallRouterEscalationPolicyTriggerParams,
        )
        from ..models.live_call_router_paging_targets_item import LiveCallRouterPagingTargetsItem

        d = src_dict.copy()
        name = d.pop("name")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        _kind = d.pop("kind", UNSET)
        kind: Union[Unset, LiveCallRouterKind]
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = LiveCallRouterKind(_kind)

        enabled = d.pop("enabled", UNSET)

        _country_code = d.pop("country_code", UNSET)
        country_code: Union[Unset, LiveCallRouterCountryCode]
        if isinstance(_country_code, Unset):
            country_code = UNSET
        else:
            country_code = LiveCallRouterCountryCode(_country_code)

        _phone_type = d.pop("phone_type", UNSET)
        phone_type: Union[Unset, LiveCallRouterPhoneType]
        if isinstance(_phone_type, Unset):
            phone_type = UNSET
        else:
            phone_type = LiveCallRouterPhoneType(_phone_type)

        phone_number = d.pop("phone_number", UNSET)

        voicemail_greeting = d.pop("voicemail_greeting", UNSET)

        caller_greeting = d.pop("caller_greeting", UNSET)

        _waiting_music_url = d.pop("waiting_music_url", UNSET)
        waiting_music_url: Union[Unset, LiveCallRouterWaitingMusicUrl]
        if isinstance(_waiting_music_url, Unset):
            waiting_music_url = UNSET
        else:
            waiting_music_url = LiveCallRouterWaitingMusicUrl(_waiting_music_url)

        sent_to_voicemail_delay = d.pop("sent_to_voicemail_delay", UNSET)

        should_redirect_to_voicemail_on_no_answer = d.pop("should_redirect_to_voicemail_on_no_answer", UNSET)

        escalation_level_delay_in_seconds = d.pop("escalation_level_delay_in_seconds", UNSET)

        should_auto_resolve_alert_on_call_end = d.pop("should_auto_resolve_alert_on_call_end", UNSET)

        alert_urgency_id = d.pop("alert_urgency_id", UNSET)

        calling_tree_prompt = d.pop("calling_tree_prompt", UNSET)

        paging_targets = []
        _paging_targets = d.pop("paging_targets", UNSET)
        for paging_targets_item_data in _paging_targets or []:
            paging_targets_item = LiveCallRouterPagingTargetsItem.from_dict(paging_targets_item_data)

            paging_targets.append(paging_targets_item)

        _escalation_policy_trigger_params = d.pop("escalation_policy_trigger_params", UNSET)
        escalation_policy_trigger_params: Union[Unset, LiveCallRouterEscalationPolicyTriggerParams]
        if isinstance(_escalation_policy_trigger_params, Unset):
            escalation_policy_trigger_params = UNSET
        else:
            escalation_policy_trigger_params = LiveCallRouterEscalationPolicyTriggerParams.from_dict(
                _escalation_policy_trigger_params
            )

        live_call_router = cls(
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            kind=kind,
            enabled=enabled,
            country_code=country_code,
            phone_type=phone_type,
            phone_number=phone_number,
            voicemail_greeting=voicemail_greeting,
            caller_greeting=caller_greeting,
            waiting_music_url=waiting_music_url,
            sent_to_voicemail_delay=sent_to_voicemail_delay,
            should_redirect_to_voicemail_on_no_answer=should_redirect_to_voicemail_on_no_answer,
            escalation_level_delay_in_seconds=escalation_level_delay_in_seconds,
            should_auto_resolve_alert_on_call_end=should_auto_resolve_alert_on_call_end,
            alert_urgency_id=alert_urgency_id,
            calling_tree_prompt=calling_tree_prompt,
            paging_targets=paging_targets,
            escalation_policy_trigger_params=escalation_policy_trigger_params,
        )

        live_call_router.additional_properties = d
        return live_call_router

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
