from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_role_data_attributes_api_keys_permissions_item import (
    UpdateRoleDataAttributesApiKeysPermissionsItem,
)
from ..models.update_role_data_attributes_audits_permissions_item import UpdateRoleDataAttributesAuditsPermissionsItem
from ..models.update_role_data_attributes_billing_permissions_item import UpdateRoleDataAttributesBillingPermissionsItem
from ..models.update_role_data_attributes_environments_permissions_item import (
    UpdateRoleDataAttributesEnvironmentsPermissionsItem,
)
from ..models.update_role_data_attributes_form_fields_permissions_item import (
    UpdateRoleDataAttributesFormFieldsPermissionsItem,
)
from ..models.update_role_data_attributes_functionalities_permissions_item import (
    UpdateRoleDataAttributesFunctionalitiesPermissionsItem,
)
from ..models.update_role_data_attributes_groups_permissions_item import UpdateRoleDataAttributesGroupsPermissionsItem
from ..models.update_role_data_attributes_incident_causes_permissions_item import (
    UpdateRoleDataAttributesIncidentCausesPermissionsItem,
)
from ..models.update_role_data_attributes_incident_feedbacks_permissions_item import (
    UpdateRoleDataAttributesIncidentFeedbacksPermissionsItem,
)
from ..models.update_role_data_attributes_incident_roles_permissions_item import (
    UpdateRoleDataAttributesIncidentRolesPermissionsItem,
)
from ..models.update_role_data_attributes_incident_types_permissions_item import (
    UpdateRoleDataAttributesIncidentTypesPermissionsItem,
)
from ..models.update_role_data_attributes_incidents_permissions_item import (
    UpdateRoleDataAttributesIncidentsPermissionsItem,
)
from ..models.update_role_data_attributes_integrations_permissions_item import (
    UpdateRoleDataAttributesIntegrationsPermissionsItem,
)
from ..models.update_role_data_attributes_invitations_permissions_item import (
    UpdateRoleDataAttributesInvitationsPermissionsItem,
)
from ..models.update_role_data_attributes_playbooks_permissions_item import (
    UpdateRoleDataAttributesPlaybooksPermissionsItem,
)
from ..models.update_role_data_attributes_private_incidents_permissions_item import (
    UpdateRoleDataAttributesPrivateIncidentsPermissionsItem,
)
from ..models.update_role_data_attributes_retrospective_permissions_item import (
    UpdateRoleDataAttributesRetrospectivePermissionsItem,
)
from ..models.update_role_data_attributes_roles_permissions_item import UpdateRoleDataAttributesRolesPermissionsItem
from ..models.update_role_data_attributes_secrets_permissions_item import UpdateRoleDataAttributesSecretsPermissionsItem
from ..models.update_role_data_attributes_services_permissions_item import (
    UpdateRoleDataAttributesServicesPermissionsItem,
)
from ..models.update_role_data_attributes_severities_permissions_item import (
    UpdateRoleDataAttributesSeveritiesPermissionsItem,
)
from ..models.update_role_data_attributes_status_pages_permissions_item import (
    UpdateRoleDataAttributesStatusPagesPermissionsItem,
)
from ..models.update_role_data_attributes_webhooks_permissions_item import (
    UpdateRoleDataAttributesWebhooksPermissionsItem,
)
from ..models.update_role_data_attributes_workflows_permissions_item import (
    UpdateRoleDataAttributesWorkflowsPermissionsItem,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateRoleDataAttributes")


@_attrs_define
class UpdateRoleDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]): The role name.
        slug (Union[Unset, str]): The role slug.
        incident_permission_set_id (Union[None, Unset, str]): Associated incident permissions set.
        api_keys_permissions (Union[Unset, list[UpdateRoleDataAttributesApiKeysPermissionsItem]]):
        audits_permissions (Union[Unset, list[UpdateRoleDataAttributesAuditsPermissionsItem]]):
        billing_permissions (Union[Unset, list[UpdateRoleDataAttributesBillingPermissionsItem]]):
        environments_permissions (Union[Unset, list[UpdateRoleDataAttributesEnvironmentsPermissionsItem]]):
        form_fields_permissions (Union[Unset, list[UpdateRoleDataAttributesFormFieldsPermissionsItem]]):
        functionalities_permissions (Union[Unset, list[UpdateRoleDataAttributesFunctionalitiesPermissionsItem]]):
        groups_permissions (Union[Unset, list[UpdateRoleDataAttributesGroupsPermissionsItem]]):
        incident_causes_permissions (Union[Unset, list[UpdateRoleDataAttributesIncidentCausesPermissionsItem]]):
        incident_feedbacks_permissions (Union[Unset, list[UpdateRoleDataAttributesIncidentFeedbacksPermissionsItem]]):
        incident_roles_permissions (Union[Unset, list[UpdateRoleDataAttributesIncidentRolesPermissionsItem]]):
        incident_types_permissions (Union[Unset, list[UpdateRoleDataAttributesIncidentTypesPermissionsItem]]):
        incidents_permissions (Union[Unset, list[UpdateRoleDataAttributesIncidentsPermissionsItem]]):
        integrations_permissions (Union[Unset, list[UpdateRoleDataAttributesIntegrationsPermissionsItem]]):
        invitations_permissions (Union[Unset, list[UpdateRoleDataAttributesInvitationsPermissionsItem]]):
        playbooks_permissions (Union[Unset, list[UpdateRoleDataAttributesPlaybooksPermissionsItem]]):
        private_incidents_permissions (Union[Unset, list[UpdateRoleDataAttributesPrivateIncidentsPermissionsItem]]):
        retrospective_permissions (Union[Unset, list[UpdateRoleDataAttributesRetrospectivePermissionsItem]]):
        roles_permissions (Union[Unset, list[UpdateRoleDataAttributesRolesPermissionsItem]]):
        secrets_permissions (Union[Unset, list[UpdateRoleDataAttributesSecretsPermissionsItem]]):
        services_permissions (Union[Unset, list[UpdateRoleDataAttributesServicesPermissionsItem]]):
        severities_permissions (Union[Unset, list[UpdateRoleDataAttributesSeveritiesPermissionsItem]]):
        status_pages_permissions (Union[Unset, list[UpdateRoleDataAttributesStatusPagesPermissionsItem]]):
        webhooks_permissions (Union[Unset, list[UpdateRoleDataAttributesWebhooksPermissionsItem]]):
        workflows_permissions (Union[Unset, list[UpdateRoleDataAttributesWorkflowsPermissionsItem]]):
    """

    name: Union[Unset, str] = UNSET
    slug: Union[Unset, str] = UNSET
    incident_permission_set_id: Union[None, Unset, str] = UNSET
    api_keys_permissions: Union[Unset, list[UpdateRoleDataAttributesApiKeysPermissionsItem]] = UNSET
    audits_permissions: Union[Unset, list[UpdateRoleDataAttributesAuditsPermissionsItem]] = UNSET
    billing_permissions: Union[Unset, list[UpdateRoleDataAttributesBillingPermissionsItem]] = UNSET
    environments_permissions: Union[Unset, list[UpdateRoleDataAttributesEnvironmentsPermissionsItem]] = UNSET
    form_fields_permissions: Union[Unset, list[UpdateRoleDataAttributesFormFieldsPermissionsItem]] = UNSET
    functionalities_permissions: Union[Unset, list[UpdateRoleDataAttributesFunctionalitiesPermissionsItem]] = UNSET
    groups_permissions: Union[Unset, list[UpdateRoleDataAttributesGroupsPermissionsItem]] = UNSET
    incident_causes_permissions: Union[Unset, list[UpdateRoleDataAttributesIncidentCausesPermissionsItem]] = UNSET
    incident_feedbacks_permissions: Union[Unset, list[UpdateRoleDataAttributesIncidentFeedbacksPermissionsItem]] = UNSET
    incident_roles_permissions: Union[Unset, list[UpdateRoleDataAttributesIncidentRolesPermissionsItem]] = UNSET
    incident_types_permissions: Union[Unset, list[UpdateRoleDataAttributesIncidentTypesPermissionsItem]] = UNSET
    incidents_permissions: Union[Unset, list[UpdateRoleDataAttributesIncidentsPermissionsItem]] = UNSET
    integrations_permissions: Union[Unset, list[UpdateRoleDataAttributesIntegrationsPermissionsItem]] = UNSET
    invitations_permissions: Union[Unset, list[UpdateRoleDataAttributesInvitationsPermissionsItem]] = UNSET
    playbooks_permissions: Union[Unset, list[UpdateRoleDataAttributesPlaybooksPermissionsItem]] = UNSET
    private_incidents_permissions: Union[Unset, list[UpdateRoleDataAttributesPrivateIncidentsPermissionsItem]] = UNSET
    retrospective_permissions: Union[Unset, list[UpdateRoleDataAttributesRetrospectivePermissionsItem]] = UNSET
    roles_permissions: Union[Unset, list[UpdateRoleDataAttributesRolesPermissionsItem]] = UNSET
    secrets_permissions: Union[Unset, list[UpdateRoleDataAttributesSecretsPermissionsItem]] = UNSET
    services_permissions: Union[Unset, list[UpdateRoleDataAttributesServicesPermissionsItem]] = UNSET
    severities_permissions: Union[Unset, list[UpdateRoleDataAttributesSeveritiesPermissionsItem]] = UNSET
    status_pages_permissions: Union[Unset, list[UpdateRoleDataAttributesStatusPagesPermissionsItem]] = UNSET
    webhooks_permissions: Union[Unset, list[UpdateRoleDataAttributesWebhooksPermissionsItem]] = UNSET
    workflows_permissions: Union[Unset, list[UpdateRoleDataAttributesWorkflowsPermissionsItem]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        incident_permission_set_id: Union[None, Unset, str]
        if isinstance(self.incident_permission_set_id, Unset):
            incident_permission_set_id = UNSET
        else:
            incident_permission_set_id = self.incident_permission_set_id

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

        billing_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.billing_permissions, Unset):
            billing_permissions = []
            for billing_permissions_item_data in self.billing_permissions:
                billing_permissions_item = billing_permissions_item_data.value
                billing_permissions.append(billing_permissions_item)

        environments_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.environments_permissions, Unset):
            environments_permissions = []
            for environments_permissions_item_data in self.environments_permissions:
                environments_permissions_item = environments_permissions_item_data.value
                environments_permissions.append(environments_permissions_item)

        form_fields_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.form_fields_permissions, Unset):
            form_fields_permissions = []
            for form_fields_permissions_item_data in self.form_fields_permissions:
                form_fields_permissions_item = form_fields_permissions_item_data.value
                form_fields_permissions.append(form_fields_permissions_item)

        functionalities_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.functionalities_permissions, Unset):
            functionalities_permissions = []
            for functionalities_permissions_item_data in self.functionalities_permissions:
                functionalities_permissions_item = functionalities_permissions_item_data.value
                functionalities_permissions.append(functionalities_permissions_item)

        groups_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.groups_permissions, Unset):
            groups_permissions = []
            for groups_permissions_item_data in self.groups_permissions:
                groups_permissions_item = groups_permissions_item_data.value
                groups_permissions.append(groups_permissions_item)

        incident_causes_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_causes_permissions, Unset):
            incident_causes_permissions = []
            for incident_causes_permissions_item_data in self.incident_causes_permissions:
                incident_causes_permissions_item = incident_causes_permissions_item_data.value
                incident_causes_permissions.append(incident_causes_permissions_item)

        incident_feedbacks_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_feedbacks_permissions, Unset):
            incident_feedbacks_permissions = []
            for incident_feedbacks_permissions_item_data in self.incident_feedbacks_permissions:
                incident_feedbacks_permissions_item = incident_feedbacks_permissions_item_data.value
                incident_feedbacks_permissions.append(incident_feedbacks_permissions_item)

        incident_roles_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_roles_permissions, Unset):
            incident_roles_permissions = []
            for incident_roles_permissions_item_data in self.incident_roles_permissions:
                incident_roles_permissions_item = incident_roles_permissions_item_data.value
                incident_roles_permissions.append(incident_roles_permissions_item)

        incident_types_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_types_permissions, Unset):
            incident_types_permissions = []
            for incident_types_permissions_item_data in self.incident_types_permissions:
                incident_types_permissions_item = incident_types_permissions_item_data.value
                incident_types_permissions.append(incident_types_permissions_item)

        incidents_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incidents_permissions, Unset):
            incidents_permissions = []
            for incidents_permissions_item_data in self.incidents_permissions:
                incidents_permissions_item = incidents_permissions_item_data.value
                incidents_permissions.append(incidents_permissions_item)

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

        playbooks_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.playbooks_permissions, Unset):
            playbooks_permissions = []
            for playbooks_permissions_item_data in self.playbooks_permissions:
                playbooks_permissions_item = playbooks_permissions_item_data.value
                playbooks_permissions.append(playbooks_permissions_item)

        private_incidents_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.private_incidents_permissions, Unset):
            private_incidents_permissions = []
            for private_incidents_permissions_item_data in self.private_incidents_permissions:
                private_incidents_permissions_item = private_incidents_permissions_item_data.value
                private_incidents_permissions.append(private_incidents_permissions_item)

        retrospective_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.retrospective_permissions, Unset):
            retrospective_permissions = []
            for retrospective_permissions_item_data in self.retrospective_permissions:
                retrospective_permissions_item = retrospective_permissions_item_data.value
                retrospective_permissions.append(retrospective_permissions_item)

        roles_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.roles_permissions, Unset):
            roles_permissions = []
            for roles_permissions_item_data in self.roles_permissions:
                roles_permissions_item = roles_permissions_item_data.value
                roles_permissions.append(roles_permissions_item)

        secrets_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.secrets_permissions, Unset):
            secrets_permissions = []
            for secrets_permissions_item_data in self.secrets_permissions:
                secrets_permissions_item = secrets_permissions_item_data.value
                secrets_permissions.append(secrets_permissions_item)

        services_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.services_permissions, Unset):
            services_permissions = []
            for services_permissions_item_data in self.services_permissions:
                services_permissions_item = services_permissions_item_data.value
                services_permissions.append(services_permissions_item)

        severities_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.severities_permissions, Unset):
            severities_permissions = []
            for severities_permissions_item_data in self.severities_permissions:
                severities_permissions_item = severities_permissions_item_data.value
                severities_permissions.append(severities_permissions_item)

        status_pages_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.status_pages_permissions, Unset):
            status_pages_permissions = []
            for status_pages_permissions_item_data in self.status_pages_permissions:
                status_pages_permissions_item = status_pages_permissions_item_data.value
                status_pages_permissions.append(status_pages_permissions_item)

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
        if incident_permission_set_id is not UNSET:
            field_dict["incident_permission_set_id"] = incident_permission_set_id
        if api_keys_permissions is not UNSET:
            field_dict["api_keys_permissions"] = api_keys_permissions
        if audits_permissions is not UNSET:
            field_dict["audits_permissions"] = audits_permissions
        if billing_permissions is not UNSET:
            field_dict["billing_permissions"] = billing_permissions
        if environments_permissions is not UNSET:
            field_dict["environments_permissions"] = environments_permissions
        if form_fields_permissions is not UNSET:
            field_dict["form_fields_permissions"] = form_fields_permissions
        if functionalities_permissions is not UNSET:
            field_dict["functionalities_permissions"] = functionalities_permissions
        if groups_permissions is not UNSET:
            field_dict["groups_permissions"] = groups_permissions
        if incident_causes_permissions is not UNSET:
            field_dict["incident_causes_permissions"] = incident_causes_permissions
        if incident_feedbacks_permissions is not UNSET:
            field_dict["incident_feedbacks_permissions"] = incident_feedbacks_permissions
        if incident_roles_permissions is not UNSET:
            field_dict["incident_roles_permissions"] = incident_roles_permissions
        if incident_types_permissions is not UNSET:
            field_dict["incident_types_permissions"] = incident_types_permissions
        if incidents_permissions is not UNSET:
            field_dict["incidents_permissions"] = incidents_permissions
        if integrations_permissions is not UNSET:
            field_dict["integrations_permissions"] = integrations_permissions
        if invitations_permissions is not UNSET:
            field_dict["invitations_permissions"] = invitations_permissions
        if playbooks_permissions is not UNSET:
            field_dict["playbooks_permissions"] = playbooks_permissions
        if private_incidents_permissions is not UNSET:
            field_dict["private_incidents_permissions"] = private_incidents_permissions
        if retrospective_permissions is not UNSET:
            field_dict["retrospective_permissions"] = retrospective_permissions
        if roles_permissions is not UNSET:
            field_dict["roles_permissions"] = roles_permissions
        if secrets_permissions is not UNSET:
            field_dict["secrets_permissions"] = secrets_permissions
        if services_permissions is not UNSET:
            field_dict["services_permissions"] = services_permissions
        if severities_permissions is not UNSET:
            field_dict["severities_permissions"] = severities_permissions
        if status_pages_permissions is not UNSET:
            field_dict["status_pages_permissions"] = status_pages_permissions
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

        def _parse_incident_permission_set_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        incident_permission_set_id = _parse_incident_permission_set_id(d.pop("incident_permission_set_id", UNSET))

        api_keys_permissions = []
        _api_keys_permissions = d.pop("api_keys_permissions", UNSET)
        for api_keys_permissions_item_data in _api_keys_permissions or []:
            api_keys_permissions_item = UpdateRoleDataAttributesApiKeysPermissionsItem(api_keys_permissions_item_data)

            api_keys_permissions.append(api_keys_permissions_item)

        audits_permissions = []
        _audits_permissions = d.pop("audits_permissions", UNSET)
        for audits_permissions_item_data in _audits_permissions or []:
            audits_permissions_item = UpdateRoleDataAttributesAuditsPermissionsItem(audits_permissions_item_data)

            audits_permissions.append(audits_permissions_item)

        billing_permissions = []
        _billing_permissions = d.pop("billing_permissions", UNSET)
        for billing_permissions_item_data in _billing_permissions or []:
            billing_permissions_item = UpdateRoleDataAttributesBillingPermissionsItem(billing_permissions_item_data)

            billing_permissions.append(billing_permissions_item)

        environments_permissions = []
        _environments_permissions = d.pop("environments_permissions", UNSET)
        for environments_permissions_item_data in _environments_permissions or []:
            environments_permissions_item = UpdateRoleDataAttributesEnvironmentsPermissionsItem(
                environments_permissions_item_data
            )

            environments_permissions.append(environments_permissions_item)

        form_fields_permissions = []
        _form_fields_permissions = d.pop("form_fields_permissions", UNSET)
        for form_fields_permissions_item_data in _form_fields_permissions or []:
            form_fields_permissions_item = UpdateRoleDataAttributesFormFieldsPermissionsItem(
                form_fields_permissions_item_data
            )

            form_fields_permissions.append(form_fields_permissions_item)

        functionalities_permissions = []
        _functionalities_permissions = d.pop("functionalities_permissions", UNSET)
        for functionalities_permissions_item_data in _functionalities_permissions or []:
            functionalities_permissions_item = UpdateRoleDataAttributesFunctionalitiesPermissionsItem(
                functionalities_permissions_item_data
            )

            functionalities_permissions.append(functionalities_permissions_item)

        groups_permissions = []
        _groups_permissions = d.pop("groups_permissions", UNSET)
        for groups_permissions_item_data in _groups_permissions or []:
            groups_permissions_item = UpdateRoleDataAttributesGroupsPermissionsItem(groups_permissions_item_data)

            groups_permissions.append(groups_permissions_item)

        incident_causes_permissions = []
        _incident_causes_permissions = d.pop("incident_causes_permissions", UNSET)
        for incident_causes_permissions_item_data in _incident_causes_permissions or []:
            incident_causes_permissions_item = UpdateRoleDataAttributesIncidentCausesPermissionsItem(
                incident_causes_permissions_item_data
            )

            incident_causes_permissions.append(incident_causes_permissions_item)

        incident_feedbacks_permissions = []
        _incident_feedbacks_permissions = d.pop("incident_feedbacks_permissions", UNSET)
        for incident_feedbacks_permissions_item_data in _incident_feedbacks_permissions or []:
            incident_feedbacks_permissions_item = UpdateRoleDataAttributesIncidentFeedbacksPermissionsItem(
                incident_feedbacks_permissions_item_data
            )

            incident_feedbacks_permissions.append(incident_feedbacks_permissions_item)

        incident_roles_permissions = []
        _incident_roles_permissions = d.pop("incident_roles_permissions", UNSET)
        for incident_roles_permissions_item_data in _incident_roles_permissions or []:
            incident_roles_permissions_item = UpdateRoleDataAttributesIncidentRolesPermissionsItem(
                incident_roles_permissions_item_data
            )

            incident_roles_permissions.append(incident_roles_permissions_item)

        incident_types_permissions = []
        _incident_types_permissions = d.pop("incident_types_permissions", UNSET)
        for incident_types_permissions_item_data in _incident_types_permissions or []:
            incident_types_permissions_item = UpdateRoleDataAttributesIncidentTypesPermissionsItem(
                incident_types_permissions_item_data
            )

            incident_types_permissions.append(incident_types_permissions_item)

        incidents_permissions = []
        _incidents_permissions = d.pop("incidents_permissions", UNSET)
        for incidents_permissions_item_data in _incidents_permissions or []:
            incidents_permissions_item = UpdateRoleDataAttributesIncidentsPermissionsItem(
                incidents_permissions_item_data
            )

            incidents_permissions.append(incidents_permissions_item)

        integrations_permissions = []
        _integrations_permissions = d.pop("integrations_permissions", UNSET)
        for integrations_permissions_item_data in _integrations_permissions or []:
            integrations_permissions_item = UpdateRoleDataAttributesIntegrationsPermissionsItem(
                integrations_permissions_item_data
            )

            integrations_permissions.append(integrations_permissions_item)

        invitations_permissions = []
        _invitations_permissions = d.pop("invitations_permissions", UNSET)
        for invitations_permissions_item_data in _invitations_permissions or []:
            invitations_permissions_item = UpdateRoleDataAttributesInvitationsPermissionsItem(
                invitations_permissions_item_data
            )

            invitations_permissions.append(invitations_permissions_item)

        playbooks_permissions = []
        _playbooks_permissions = d.pop("playbooks_permissions", UNSET)
        for playbooks_permissions_item_data in _playbooks_permissions or []:
            playbooks_permissions_item = UpdateRoleDataAttributesPlaybooksPermissionsItem(
                playbooks_permissions_item_data
            )

            playbooks_permissions.append(playbooks_permissions_item)

        private_incidents_permissions = []
        _private_incidents_permissions = d.pop("private_incidents_permissions", UNSET)
        for private_incidents_permissions_item_data in _private_incidents_permissions or []:
            private_incidents_permissions_item = UpdateRoleDataAttributesPrivateIncidentsPermissionsItem(
                private_incidents_permissions_item_data
            )

            private_incidents_permissions.append(private_incidents_permissions_item)

        retrospective_permissions = []
        _retrospective_permissions = d.pop("retrospective_permissions", UNSET)
        for retrospective_permissions_item_data in _retrospective_permissions or []:
            retrospective_permissions_item = UpdateRoleDataAttributesRetrospectivePermissionsItem(
                retrospective_permissions_item_data
            )

            retrospective_permissions.append(retrospective_permissions_item)

        roles_permissions = []
        _roles_permissions = d.pop("roles_permissions", UNSET)
        for roles_permissions_item_data in _roles_permissions or []:
            roles_permissions_item = UpdateRoleDataAttributesRolesPermissionsItem(roles_permissions_item_data)

            roles_permissions.append(roles_permissions_item)

        secrets_permissions = []
        _secrets_permissions = d.pop("secrets_permissions", UNSET)
        for secrets_permissions_item_data in _secrets_permissions or []:
            secrets_permissions_item = UpdateRoleDataAttributesSecretsPermissionsItem(secrets_permissions_item_data)

            secrets_permissions.append(secrets_permissions_item)

        services_permissions = []
        _services_permissions = d.pop("services_permissions", UNSET)
        for services_permissions_item_data in _services_permissions or []:
            services_permissions_item = UpdateRoleDataAttributesServicesPermissionsItem(services_permissions_item_data)

            services_permissions.append(services_permissions_item)

        severities_permissions = []
        _severities_permissions = d.pop("severities_permissions", UNSET)
        for severities_permissions_item_data in _severities_permissions or []:
            severities_permissions_item = UpdateRoleDataAttributesSeveritiesPermissionsItem(
                severities_permissions_item_data
            )

            severities_permissions.append(severities_permissions_item)

        status_pages_permissions = []
        _status_pages_permissions = d.pop("status_pages_permissions", UNSET)
        for status_pages_permissions_item_data in _status_pages_permissions or []:
            status_pages_permissions_item = UpdateRoleDataAttributesStatusPagesPermissionsItem(
                status_pages_permissions_item_data
            )

            status_pages_permissions.append(status_pages_permissions_item)

        webhooks_permissions = []
        _webhooks_permissions = d.pop("webhooks_permissions", UNSET)
        for webhooks_permissions_item_data in _webhooks_permissions or []:
            webhooks_permissions_item = UpdateRoleDataAttributesWebhooksPermissionsItem(webhooks_permissions_item_data)

            webhooks_permissions.append(webhooks_permissions_item)

        workflows_permissions = []
        _workflows_permissions = d.pop("workflows_permissions", UNSET)
        for workflows_permissions_item_data in _workflows_permissions or []:
            workflows_permissions_item = UpdateRoleDataAttributesWorkflowsPermissionsItem(
                workflows_permissions_item_data
            )

            workflows_permissions.append(workflows_permissions_item)

        update_role_data_attributes = cls(
            name=name,
            slug=slug,
            incident_permission_set_id=incident_permission_set_id,
            api_keys_permissions=api_keys_permissions,
            audits_permissions=audits_permissions,
            billing_permissions=billing_permissions,
            environments_permissions=environments_permissions,
            form_fields_permissions=form_fields_permissions,
            functionalities_permissions=functionalities_permissions,
            groups_permissions=groups_permissions,
            incident_causes_permissions=incident_causes_permissions,
            incident_feedbacks_permissions=incident_feedbacks_permissions,
            incident_roles_permissions=incident_roles_permissions,
            incident_types_permissions=incident_types_permissions,
            incidents_permissions=incidents_permissions,
            integrations_permissions=integrations_permissions,
            invitations_permissions=invitations_permissions,
            playbooks_permissions=playbooks_permissions,
            private_incidents_permissions=private_incidents_permissions,
            retrospective_permissions=retrospective_permissions,
            roles_permissions=roles_permissions,
            secrets_permissions=secrets_permissions,
            services_permissions=services_permissions,
            severities_permissions=severities_permissions,
            status_pages_permissions=status_pages_permissions,
            webhooks_permissions=webhooks_permissions,
            workflows_permissions=workflows_permissions,
        )

        return update_role_data_attributes
