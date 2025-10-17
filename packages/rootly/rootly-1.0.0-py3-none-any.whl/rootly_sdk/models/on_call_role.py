from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.on_call_role_alert_sources_permissions_item import OnCallRoleAlertSourcesPermissionsItem
from ..models.on_call_role_alert_urgency_permissions_item import OnCallRoleAlertUrgencyPermissionsItem
from ..models.on_call_role_alerts_permissions_item import OnCallRoleAlertsPermissionsItem
from ..models.on_call_role_api_keys_permissions_item import OnCallRoleApiKeysPermissionsItem
from ..models.on_call_role_audits_permissions_item import OnCallRoleAuditsPermissionsItem
from ..models.on_call_role_contacts_permissions_item import OnCallRoleContactsPermissionsItem
from ..models.on_call_role_escalation_policies_permissions_item import OnCallRoleEscalationPoliciesPermissionsItem
from ..models.on_call_role_groups_permissions_item import OnCallRoleGroupsPermissionsItem
from ..models.on_call_role_heartbeats_permissions_item import OnCallRoleHeartbeatsPermissionsItem
from ..models.on_call_role_integrations_permissions_item import OnCallRoleIntegrationsPermissionsItem
from ..models.on_call_role_invitations_permissions_item import OnCallRoleInvitationsPermissionsItem
from ..models.on_call_role_live_call_routing_permissions_item import OnCallRoleLiveCallRoutingPermissionsItem
from ..models.on_call_role_schedule_override_permissions_item import OnCallRoleScheduleOverridePermissionsItem
from ..models.on_call_role_schedules_permissions_item import OnCallRoleSchedulesPermissionsItem
from ..models.on_call_role_services_permissions_item import OnCallRoleServicesPermissionsItem
from ..models.on_call_role_webhooks_permissions_item import OnCallRoleWebhooksPermissionsItem
from ..models.on_call_role_workflows_permissions_item import OnCallRoleWorkflowsPermissionsItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="OnCallRole")


@_attrs_define
class OnCallRole:
    """
    Attributes:
        name (str): The role name.
        slug (str): The role slug.
        system_role (str): The kind of role
        created_at (str):
        updated_at (str):
        alert_sources_permissions (Union[Unset, list[OnCallRoleAlertSourcesPermissionsItem]]):
        alert_urgency_permissions (Union[Unset, list[OnCallRoleAlertUrgencyPermissionsItem]]):
        alerts_permissions (Union[Unset, list[OnCallRoleAlertsPermissionsItem]]):
        api_keys_permissions (Union[Unset, list[OnCallRoleApiKeysPermissionsItem]]):
        audits_permissions (Union[Unset, list[OnCallRoleAuditsPermissionsItem]]):
        contacts_permissions (Union[Unset, list[OnCallRoleContactsPermissionsItem]]):
        escalation_policies_permissions (Union[Unset, list[OnCallRoleEscalationPoliciesPermissionsItem]]):
        groups_permissions (Union[Unset, list[OnCallRoleGroupsPermissionsItem]]):
        heartbeats_permissions (Union[Unset, list[OnCallRoleHeartbeatsPermissionsItem]]):
        integrations_permissions (Union[Unset, list[OnCallRoleIntegrationsPermissionsItem]]):
        invitations_permissions (Union[Unset, list[OnCallRoleInvitationsPermissionsItem]]):
        live_call_routing_permissions (Union[Unset, list[OnCallRoleLiveCallRoutingPermissionsItem]]):
        schedule_override_permissions (Union[Unset, list[OnCallRoleScheduleOverridePermissionsItem]]):
        schedules_permissions (Union[Unset, list[OnCallRoleSchedulesPermissionsItem]]):
        services_permissions (Union[Unset, list[OnCallRoleServicesPermissionsItem]]):
        webhooks_permissions (Union[Unset, list[OnCallRoleWebhooksPermissionsItem]]):
        workflows_permissions (Union[Unset, list[OnCallRoleWorkflowsPermissionsItem]]):
    """

    name: str
    slug: str
    system_role: str
    created_at: str
    updated_at: str
    alert_sources_permissions: Union[Unset, list[OnCallRoleAlertSourcesPermissionsItem]] = UNSET
    alert_urgency_permissions: Union[Unset, list[OnCallRoleAlertUrgencyPermissionsItem]] = UNSET
    alerts_permissions: Union[Unset, list[OnCallRoleAlertsPermissionsItem]] = UNSET
    api_keys_permissions: Union[Unset, list[OnCallRoleApiKeysPermissionsItem]] = UNSET
    audits_permissions: Union[Unset, list[OnCallRoleAuditsPermissionsItem]] = UNSET
    contacts_permissions: Union[Unset, list[OnCallRoleContactsPermissionsItem]] = UNSET
    escalation_policies_permissions: Union[Unset, list[OnCallRoleEscalationPoliciesPermissionsItem]] = UNSET
    groups_permissions: Union[Unset, list[OnCallRoleGroupsPermissionsItem]] = UNSET
    heartbeats_permissions: Union[Unset, list[OnCallRoleHeartbeatsPermissionsItem]] = UNSET
    integrations_permissions: Union[Unset, list[OnCallRoleIntegrationsPermissionsItem]] = UNSET
    invitations_permissions: Union[Unset, list[OnCallRoleInvitationsPermissionsItem]] = UNSET
    live_call_routing_permissions: Union[Unset, list[OnCallRoleLiveCallRoutingPermissionsItem]] = UNSET
    schedule_override_permissions: Union[Unset, list[OnCallRoleScheduleOverridePermissionsItem]] = UNSET
    schedules_permissions: Union[Unset, list[OnCallRoleSchedulesPermissionsItem]] = UNSET
    services_permissions: Union[Unset, list[OnCallRoleServicesPermissionsItem]] = UNSET
    webhooks_permissions: Union[Unset, list[OnCallRoleWebhooksPermissionsItem]] = UNSET
    workflows_permissions: Union[Unset, list[OnCallRoleWorkflowsPermissionsItem]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        system_role = self.system_role

        created_at = self.created_at

        updated_at = self.updated_at

        alert_sources_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.alert_sources_permissions, Unset):
            alert_sources_permissions = []
            for alert_sources_permissions_item_data in self.alert_sources_permissions:
                alert_sources_permissions_item = alert_sources_permissions_item_data.value
                alert_sources_permissions.append(alert_sources_permissions_item)

        alert_urgency_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.alert_urgency_permissions, Unset):
            alert_urgency_permissions = []
            for alert_urgency_permissions_item_data in self.alert_urgency_permissions:
                alert_urgency_permissions_item = alert_urgency_permissions_item_data.value
                alert_urgency_permissions.append(alert_urgency_permissions_item)

        alerts_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.alerts_permissions, Unset):
            alerts_permissions = []
            for alerts_permissions_item_data in self.alerts_permissions:
                alerts_permissions_item = alerts_permissions_item_data.value
                alerts_permissions.append(alerts_permissions_item)

        api_keys_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.api_keys_permissions, Unset):
            api_keys_permissions = []
            for api_keys_permissions_item_data in self.api_keys_permissions:
                api_keys_permissions_item = api_keys_permissions_item_data.value
                api_keys_permissions.append(api_keys_permissions_item)

        audits_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.audits_permissions, Unset):
            audits_permissions = []
            for audits_permissions_item_data in self.audits_permissions:
                audits_permissions_item = audits_permissions_item_data.value
                audits_permissions.append(audits_permissions_item)

        contacts_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.contacts_permissions, Unset):
            contacts_permissions = []
            for contacts_permissions_item_data in self.contacts_permissions:
                contacts_permissions_item = contacts_permissions_item_data.value
                contacts_permissions.append(contacts_permissions_item)

        escalation_policies_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.escalation_policies_permissions, Unset):
            escalation_policies_permissions = []
            for escalation_policies_permissions_item_data in self.escalation_policies_permissions:
                escalation_policies_permissions_item = escalation_policies_permissions_item_data.value
                escalation_policies_permissions.append(escalation_policies_permissions_item)

        groups_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.groups_permissions, Unset):
            groups_permissions = []
            for groups_permissions_item_data in self.groups_permissions:
                groups_permissions_item = groups_permissions_item_data.value
                groups_permissions.append(groups_permissions_item)

        heartbeats_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.heartbeats_permissions, Unset):
            heartbeats_permissions = []
            for heartbeats_permissions_item_data in self.heartbeats_permissions:
                heartbeats_permissions_item = heartbeats_permissions_item_data.value
                heartbeats_permissions.append(heartbeats_permissions_item)

        integrations_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.integrations_permissions, Unset):
            integrations_permissions = []
            for integrations_permissions_item_data in self.integrations_permissions:
                integrations_permissions_item = integrations_permissions_item_data.value
                integrations_permissions.append(integrations_permissions_item)

        invitations_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.invitations_permissions, Unset):
            invitations_permissions = []
            for invitations_permissions_item_data in self.invitations_permissions:
                invitations_permissions_item = invitations_permissions_item_data.value
                invitations_permissions.append(invitations_permissions_item)

        live_call_routing_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.live_call_routing_permissions, Unset):
            live_call_routing_permissions = []
            for live_call_routing_permissions_item_data in self.live_call_routing_permissions:
                live_call_routing_permissions_item = live_call_routing_permissions_item_data.value
                live_call_routing_permissions.append(live_call_routing_permissions_item)

        schedule_override_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.schedule_override_permissions, Unset):
            schedule_override_permissions = []
            for schedule_override_permissions_item_data in self.schedule_override_permissions:
                schedule_override_permissions_item = schedule_override_permissions_item_data.value
                schedule_override_permissions.append(schedule_override_permissions_item)

        schedules_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.schedules_permissions, Unset):
            schedules_permissions = []
            for schedules_permissions_item_data in self.schedules_permissions:
                schedules_permissions_item = schedules_permissions_item_data.value
                schedules_permissions.append(schedules_permissions_item)

        services_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.services_permissions, Unset):
            services_permissions = []
            for services_permissions_item_data in self.services_permissions:
                services_permissions_item = services_permissions_item_data.value
                services_permissions.append(services_permissions_item)

        webhooks_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.webhooks_permissions, Unset):
            webhooks_permissions = []
            for webhooks_permissions_item_data in self.webhooks_permissions:
                webhooks_permissions_item = webhooks_permissions_item_data.value
                webhooks_permissions.append(webhooks_permissions_item)

        workflows_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.workflows_permissions, Unset):
            workflows_permissions = []
            for workflows_permissions_item_data in self.workflows_permissions:
                workflows_permissions_item = workflows_permissions_item_data.value
                workflows_permissions.append(workflows_permissions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "slug": slug,
                "system_role": system_role,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if alert_sources_permissions is not UNSET:
            field_dict["alert_sources_permissions"] = alert_sources_permissions
        if alert_urgency_permissions is not UNSET:
            field_dict["alert_urgency_permissions"] = alert_urgency_permissions
        if alerts_permissions is not UNSET:
            field_dict["alerts_permissions"] = alerts_permissions
        if api_keys_permissions is not UNSET:
            field_dict["api_keys_permissions"] = api_keys_permissions
        if audits_permissions is not UNSET:
            field_dict["audits_permissions"] = audits_permissions
        if contacts_permissions is not UNSET:
            field_dict["contacts_permissions"] = contacts_permissions
        if escalation_policies_permissions is not UNSET:
            field_dict["escalation_policies_permissions"] = escalation_policies_permissions
        if groups_permissions is not UNSET:
            field_dict["groups_permissions"] = groups_permissions
        if heartbeats_permissions is not UNSET:
            field_dict["heartbeats_permissions"] = heartbeats_permissions
        if integrations_permissions is not UNSET:
            field_dict["integrations_permissions"] = integrations_permissions
        if invitations_permissions is not UNSET:
            field_dict["invitations_permissions"] = invitations_permissions
        if live_call_routing_permissions is not UNSET:
            field_dict["live_call_routing_permissions"] = live_call_routing_permissions
        if schedule_override_permissions is not UNSET:
            field_dict["schedule_override_permissions"] = schedule_override_permissions
        if schedules_permissions is not UNSET:
            field_dict["schedules_permissions"] = schedules_permissions
        if services_permissions is not UNSET:
            field_dict["services_permissions"] = services_permissions
        if webhooks_permissions is not UNSET:
            field_dict["webhooks_permissions"] = webhooks_permissions
        if workflows_permissions is not UNSET:
            field_dict["workflows_permissions"] = workflows_permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        slug = d.pop("slug")

        system_role = d.pop("system_role")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        alert_sources_permissions = []
        _alert_sources_permissions = d.pop("alert_sources_permissions", UNSET)
        for alert_sources_permissions_item_data in _alert_sources_permissions or []:
            alert_sources_permissions_item = OnCallRoleAlertSourcesPermissionsItem(alert_sources_permissions_item_data)

            alert_sources_permissions.append(alert_sources_permissions_item)

        alert_urgency_permissions = []
        _alert_urgency_permissions = d.pop("alert_urgency_permissions", UNSET)
        for alert_urgency_permissions_item_data in _alert_urgency_permissions or []:
            alert_urgency_permissions_item = OnCallRoleAlertUrgencyPermissionsItem(alert_urgency_permissions_item_data)

            alert_urgency_permissions.append(alert_urgency_permissions_item)

        alerts_permissions = []
        _alerts_permissions = d.pop("alerts_permissions", UNSET)
        for alerts_permissions_item_data in _alerts_permissions or []:
            alerts_permissions_item = OnCallRoleAlertsPermissionsItem(alerts_permissions_item_data)

            alerts_permissions.append(alerts_permissions_item)

        api_keys_permissions = []
        _api_keys_permissions = d.pop("api_keys_permissions", UNSET)
        for api_keys_permissions_item_data in _api_keys_permissions or []:
            api_keys_permissions_item = OnCallRoleApiKeysPermissionsItem(api_keys_permissions_item_data)

            api_keys_permissions.append(api_keys_permissions_item)

        audits_permissions = []
        _audits_permissions = d.pop("audits_permissions", UNSET)
        for audits_permissions_item_data in _audits_permissions or []:
            audits_permissions_item = OnCallRoleAuditsPermissionsItem(audits_permissions_item_data)

            audits_permissions.append(audits_permissions_item)

        contacts_permissions = []
        _contacts_permissions = d.pop("contacts_permissions", UNSET)
        for contacts_permissions_item_data in _contacts_permissions or []:
            contacts_permissions_item = OnCallRoleContactsPermissionsItem(contacts_permissions_item_data)

            contacts_permissions.append(contacts_permissions_item)

        escalation_policies_permissions = []
        _escalation_policies_permissions = d.pop("escalation_policies_permissions", UNSET)
        for escalation_policies_permissions_item_data in _escalation_policies_permissions or []:
            escalation_policies_permissions_item = OnCallRoleEscalationPoliciesPermissionsItem(
                escalation_policies_permissions_item_data
            )

            escalation_policies_permissions.append(escalation_policies_permissions_item)

        groups_permissions = []
        _groups_permissions = d.pop("groups_permissions", UNSET)
        for groups_permissions_item_data in _groups_permissions or []:
            groups_permissions_item = OnCallRoleGroupsPermissionsItem(groups_permissions_item_data)

            groups_permissions.append(groups_permissions_item)

        heartbeats_permissions = []
        _heartbeats_permissions = d.pop("heartbeats_permissions", UNSET)
        for heartbeats_permissions_item_data in _heartbeats_permissions or []:
            heartbeats_permissions_item = OnCallRoleHeartbeatsPermissionsItem(heartbeats_permissions_item_data)

            heartbeats_permissions.append(heartbeats_permissions_item)

        integrations_permissions = []
        _integrations_permissions = d.pop("integrations_permissions", UNSET)
        for integrations_permissions_item_data in _integrations_permissions or []:
            integrations_permissions_item = OnCallRoleIntegrationsPermissionsItem(integrations_permissions_item_data)

            integrations_permissions.append(integrations_permissions_item)

        invitations_permissions = []
        _invitations_permissions = d.pop("invitations_permissions", UNSET)
        for invitations_permissions_item_data in _invitations_permissions or []:
            invitations_permissions_item = OnCallRoleInvitationsPermissionsItem(invitations_permissions_item_data)

            invitations_permissions.append(invitations_permissions_item)

        live_call_routing_permissions = []
        _live_call_routing_permissions = d.pop("live_call_routing_permissions", UNSET)
        for live_call_routing_permissions_item_data in _live_call_routing_permissions or []:
            live_call_routing_permissions_item = OnCallRoleLiveCallRoutingPermissionsItem(
                live_call_routing_permissions_item_data
            )

            live_call_routing_permissions.append(live_call_routing_permissions_item)

        schedule_override_permissions = []
        _schedule_override_permissions = d.pop("schedule_override_permissions", UNSET)
        for schedule_override_permissions_item_data in _schedule_override_permissions or []:
            schedule_override_permissions_item = OnCallRoleScheduleOverridePermissionsItem(
                schedule_override_permissions_item_data
            )

            schedule_override_permissions.append(schedule_override_permissions_item)

        schedules_permissions = []
        _schedules_permissions = d.pop("schedules_permissions", UNSET)
        for schedules_permissions_item_data in _schedules_permissions or []:
            schedules_permissions_item = OnCallRoleSchedulesPermissionsItem(schedules_permissions_item_data)

            schedules_permissions.append(schedules_permissions_item)

        services_permissions = []
        _services_permissions = d.pop("services_permissions", UNSET)
        for services_permissions_item_data in _services_permissions or []:
            services_permissions_item = OnCallRoleServicesPermissionsItem(services_permissions_item_data)

            services_permissions.append(services_permissions_item)

        webhooks_permissions = []
        _webhooks_permissions = d.pop("webhooks_permissions", UNSET)
        for webhooks_permissions_item_data in _webhooks_permissions or []:
            webhooks_permissions_item = OnCallRoleWebhooksPermissionsItem(webhooks_permissions_item_data)

            webhooks_permissions.append(webhooks_permissions_item)

        workflows_permissions = []
        _workflows_permissions = d.pop("workflows_permissions", UNSET)
        for workflows_permissions_item_data in _workflows_permissions or []:
            workflows_permissions_item = OnCallRoleWorkflowsPermissionsItem(workflows_permissions_item_data)

            workflows_permissions.append(workflows_permissions_item)

        on_call_role = cls(
            name=name,
            slug=slug,
            system_role=system_role,
            created_at=created_at,
            updated_at=updated_at,
            alert_sources_permissions=alert_sources_permissions,
            alert_urgency_permissions=alert_urgency_permissions,
            alerts_permissions=alerts_permissions,
            api_keys_permissions=api_keys_permissions,
            audits_permissions=audits_permissions,
            contacts_permissions=contacts_permissions,
            escalation_policies_permissions=escalation_policies_permissions,
            groups_permissions=groups_permissions,
            heartbeats_permissions=heartbeats_permissions,
            integrations_permissions=integrations_permissions,
            invitations_permissions=invitations_permissions,
            live_call_routing_permissions=live_call_routing_permissions,
            schedule_override_permissions=schedule_override_permissions,
            schedules_permissions=schedules_permissions,
            services_permissions=services_permissions,
            webhooks_permissions=webhooks_permissions,
            workflows_permissions=workflows_permissions,
        )

        on_call_role.additional_properties = d
        return on_call_role

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
