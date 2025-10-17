from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.update_on_call_role_data_attributes_alert_sources_permissions_item import (
    UpdateOnCallRoleDataAttributesAlertSourcesPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_alert_urgency_permissions_item import (
    UpdateOnCallRoleDataAttributesAlertUrgencyPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_alerts_permissions_item import (
    UpdateOnCallRoleDataAttributesAlertsPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_api_keys_permissions_item import (
    UpdateOnCallRoleDataAttributesApiKeysPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_audits_permissions_item import (
    UpdateOnCallRoleDataAttributesAuditsPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_contacts_permissions_item import (
    UpdateOnCallRoleDataAttributesContactsPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_escalation_policies_permissions_item import (
    UpdateOnCallRoleDataAttributesEscalationPoliciesPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_groups_permissions_item import (
    UpdateOnCallRoleDataAttributesGroupsPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_heartbeats_permissions_item import (
    UpdateOnCallRoleDataAttributesHeartbeatsPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_integrations_permissions_item import (
    UpdateOnCallRoleDataAttributesIntegrationsPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_invitations_permissions_item import (
    UpdateOnCallRoleDataAttributesInvitationsPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_live_call_routing_permissions_item import (
    UpdateOnCallRoleDataAttributesLiveCallRoutingPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_schedule_override_permissions_item import (
    UpdateOnCallRoleDataAttributesScheduleOverridePermissionsItem,
)
from ..models.update_on_call_role_data_attributes_schedules_permissions_item import (
    UpdateOnCallRoleDataAttributesSchedulesPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_services_permissions_item import (
    UpdateOnCallRoleDataAttributesServicesPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_webhooks_permissions_item import (
    UpdateOnCallRoleDataAttributesWebhooksPermissionsItem,
)
from ..models.update_on_call_role_data_attributes_workflows_permissions_item import (
    UpdateOnCallRoleDataAttributesWorkflowsPermissionsItem,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateOnCallRoleDataAttributes")


@_attrs_define
class UpdateOnCallRoleDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]): The role name.
        slug (Union[Unset, str]): The role slug.
        system_role (Union[Unset, str]): The kind of role (user and custom type roles are only editable)
        alert_sources_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesAlertSourcesPermissionsItem]]):
        alert_urgency_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesAlertUrgencyPermissionsItem]]):
        alerts_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesAlertsPermissionsItem]]):
        api_keys_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesApiKeysPermissionsItem]]):
        audits_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesAuditsPermissionsItem]]):
        contacts_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesContactsPermissionsItem]]):
        escalation_policies_permissions (Union[Unset,
            list[UpdateOnCallRoleDataAttributesEscalationPoliciesPermissionsItem]]):
        groups_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesGroupsPermissionsItem]]):
        heartbeats_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesHeartbeatsPermissionsItem]]):
        integrations_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesIntegrationsPermissionsItem]]):
        invitations_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesInvitationsPermissionsItem]]):
        live_call_routing_permissions (Union[Unset,
            list[UpdateOnCallRoleDataAttributesLiveCallRoutingPermissionsItem]]):
        schedule_override_permissions (Union[Unset,
            list[UpdateOnCallRoleDataAttributesScheduleOverridePermissionsItem]]):
        schedules_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesSchedulesPermissionsItem]]):
        services_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesServicesPermissionsItem]]):
        webhooks_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesWebhooksPermissionsItem]]):
        workflows_permissions (Union[Unset, list[UpdateOnCallRoleDataAttributesWorkflowsPermissionsItem]]):
    """

    name: Union[Unset, str] = UNSET
    slug: Union[Unset, str] = UNSET
    system_role: Union[Unset, str] = UNSET
    alert_sources_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesAlertSourcesPermissionsItem]] = UNSET
    alert_urgency_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesAlertUrgencyPermissionsItem]] = UNSET
    alerts_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesAlertsPermissionsItem]] = UNSET
    api_keys_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesApiKeysPermissionsItem]] = UNSET
    audits_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesAuditsPermissionsItem]] = UNSET
    contacts_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesContactsPermissionsItem]] = UNSET
    escalation_policies_permissions: Union[
        Unset, list[UpdateOnCallRoleDataAttributesEscalationPoliciesPermissionsItem]
    ] = UNSET
    groups_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesGroupsPermissionsItem]] = UNSET
    heartbeats_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesHeartbeatsPermissionsItem]] = UNSET
    integrations_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesIntegrationsPermissionsItem]] = UNSET
    invitations_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesInvitationsPermissionsItem]] = UNSET
    live_call_routing_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesLiveCallRoutingPermissionsItem]] = (
        UNSET
    )
    schedule_override_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesScheduleOverridePermissionsItem]] = (
        UNSET
    )
    schedules_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesSchedulesPermissionsItem]] = UNSET
    services_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesServicesPermissionsItem]] = UNSET
    webhooks_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesWebhooksPermissionsItem]] = UNSET
    workflows_permissions: Union[Unset, list[UpdateOnCallRoleDataAttributesWorkflowsPermissionsItem]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        system_role = self.system_role

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
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if slug is not UNSET:
            field_dict["slug"] = slug
        if system_role is not UNSET:
            field_dict["system_role"] = system_role
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
        name = d.pop("name", UNSET)

        slug = d.pop("slug", UNSET)

        system_role = d.pop("system_role", UNSET)

        alert_sources_permissions = []
        _alert_sources_permissions = d.pop("alert_sources_permissions", UNSET)
        for alert_sources_permissions_item_data in _alert_sources_permissions or []:
            alert_sources_permissions_item = UpdateOnCallRoleDataAttributesAlertSourcesPermissionsItem(
                alert_sources_permissions_item_data
            )

            alert_sources_permissions.append(alert_sources_permissions_item)

        alert_urgency_permissions = []
        _alert_urgency_permissions = d.pop("alert_urgency_permissions", UNSET)
        for alert_urgency_permissions_item_data in _alert_urgency_permissions or []:
            alert_urgency_permissions_item = UpdateOnCallRoleDataAttributesAlertUrgencyPermissionsItem(
                alert_urgency_permissions_item_data
            )

            alert_urgency_permissions.append(alert_urgency_permissions_item)

        alerts_permissions = []
        _alerts_permissions = d.pop("alerts_permissions", UNSET)
        for alerts_permissions_item_data in _alerts_permissions or []:
            alerts_permissions_item = UpdateOnCallRoleDataAttributesAlertsPermissionsItem(alerts_permissions_item_data)

            alerts_permissions.append(alerts_permissions_item)

        api_keys_permissions = []
        _api_keys_permissions = d.pop("api_keys_permissions", UNSET)
        for api_keys_permissions_item_data in _api_keys_permissions or []:
            api_keys_permissions_item = UpdateOnCallRoleDataAttributesApiKeysPermissionsItem(
                api_keys_permissions_item_data
            )

            api_keys_permissions.append(api_keys_permissions_item)

        audits_permissions = []
        _audits_permissions = d.pop("audits_permissions", UNSET)
        for audits_permissions_item_data in _audits_permissions or []:
            audits_permissions_item = UpdateOnCallRoleDataAttributesAuditsPermissionsItem(audits_permissions_item_data)

            audits_permissions.append(audits_permissions_item)

        contacts_permissions = []
        _contacts_permissions = d.pop("contacts_permissions", UNSET)
        for contacts_permissions_item_data in _contacts_permissions or []:
            contacts_permissions_item = UpdateOnCallRoleDataAttributesContactsPermissionsItem(
                contacts_permissions_item_data
            )

            contacts_permissions.append(contacts_permissions_item)

        escalation_policies_permissions = []
        _escalation_policies_permissions = d.pop("escalation_policies_permissions", UNSET)
        for escalation_policies_permissions_item_data in _escalation_policies_permissions or []:
            escalation_policies_permissions_item = UpdateOnCallRoleDataAttributesEscalationPoliciesPermissionsItem(
                escalation_policies_permissions_item_data
            )

            escalation_policies_permissions.append(escalation_policies_permissions_item)

        groups_permissions = []
        _groups_permissions = d.pop("groups_permissions", UNSET)
        for groups_permissions_item_data in _groups_permissions or []:
            groups_permissions_item = UpdateOnCallRoleDataAttributesGroupsPermissionsItem(groups_permissions_item_data)

            groups_permissions.append(groups_permissions_item)

        heartbeats_permissions = []
        _heartbeats_permissions = d.pop("heartbeats_permissions", UNSET)
        for heartbeats_permissions_item_data in _heartbeats_permissions or []:
            heartbeats_permissions_item = UpdateOnCallRoleDataAttributesHeartbeatsPermissionsItem(
                heartbeats_permissions_item_data
            )

            heartbeats_permissions.append(heartbeats_permissions_item)

        integrations_permissions = []
        _integrations_permissions = d.pop("integrations_permissions", UNSET)
        for integrations_permissions_item_data in _integrations_permissions or []:
            integrations_permissions_item = UpdateOnCallRoleDataAttributesIntegrationsPermissionsItem(
                integrations_permissions_item_data
            )

            integrations_permissions.append(integrations_permissions_item)

        invitations_permissions = []
        _invitations_permissions = d.pop("invitations_permissions", UNSET)
        for invitations_permissions_item_data in _invitations_permissions or []:
            invitations_permissions_item = UpdateOnCallRoleDataAttributesInvitationsPermissionsItem(
                invitations_permissions_item_data
            )

            invitations_permissions.append(invitations_permissions_item)

        live_call_routing_permissions = []
        _live_call_routing_permissions = d.pop("live_call_routing_permissions", UNSET)
        for live_call_routing_permissions_item_data in _live_call_routing_permissions or []:
            live_call_routing_permissions_item = UpdateOnCallRoleDataAttributesLiveCallRoutingPermissionsItem(
                live_call_routing_permissions_item_data
            )

            live_call_routing_permissions.append(live_call_routing_permissions_item)

        schedule_override_permissions = []
        _schedule_override_permissions = d.pop("schedule_override_permissions", UNSET)
        for schedule_override_permissions_item_data in _schedule_override_permissions or []:
            schedule_override_permissions_item = UpdateOnCallRoleDataAttributesScheduleOverridePermissionsItem(
                schedule_override_permissions_item_data
            )

            schedule_override_permissions.append(schedule_override_permissions_item)

        schedules_permissions = []
        _schedules_permissions = d.pop("schedules_permissions", UNSET)
        for schedules_permissions_item_data in _schedules_permissions or []:
            schedules_permissions_item = UpdateOnCallRoleDataAttributesSchedulesPermissionsItem(
                schedules_permissions_item_data
            )

            schedules_permissions.append(schedules_permissions_item)

        services_permissions = []
        _services_permissions = d.pop("services_permissions", UNSET)
        for services_permissions_item_data in _services_permissions or []:
            services_permissions_item = UpdateOnCallRoleDataAttributesServicesPermissionsItem(
                services_permissions_item_data
            )

            services_permissions.append(services_permissions_item)

        webhooks_permissions = []
        _webhooks_permissions = d.pop("webhooks_permissions", UNSET)
        for webhooks_permissions_item_data in _webhooks_permissions or []:
            webhooks_permissions_item = UpdateOnCallRoleDataAttributesWebhooksPermissionsItem(
                webhooks_permissions_item_data
            )

            webhooks_permissions.append(webhooks_permissions_item)

        workflows_permissions = []
        _workflows_permissions = d.pop("workflows_permissions", UNSET)
        for workflows_permissions_item_data in _workflows_permissions or []:
            workflows_permissions_item = UpdateOnCallRoleDataAttributesWorkflowsPermissionsItem(
                workflows_permissions_item_data
            )

            workflows_permissions.append(workflows_permissions_item)

        update_on_call_role_data_attributes = cls(
            name=name,
            slug=slug,
            system_role=system_role,
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

        return update_on_call_role_data_attributes
