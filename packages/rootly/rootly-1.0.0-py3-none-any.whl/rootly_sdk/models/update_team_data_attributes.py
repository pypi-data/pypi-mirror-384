from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_team_data_attributes_slack_aliases_type_0_item import (
        UpdateTeamDataAttributesSlackAliasesType0Item,
    )
    from ..models.update_team_data_attributes_slack_channels_type_0_item import (
        UpdateTeamDataAttributesSlackChannelsType0Item,
    )


T = TypeVar("T", bound="UpdateTeamDataAttributes")


@_attrs_define
class UpdateTeamDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]): The name of the team
        description (Union[None, Unset, str]): The description of the team
        notify_emails (Union[None, Unset, list[str]]): Emails to attach to the team
        color (Union[None, Unset, str]): The hex color of the team
        position (Union[None, Unset, int]): Position of the team
        backstage_id (Union[None, Unset, str]): The Backstage entity id associated to this team. eg:
            :namespace/:kind/:entity_name
        external_id (Union[None, Unset, str]): The external id associated to this team
        pagerduty_id (Union[None, Unset, str]): The PagerDuty group id associated to this team
        pagerduty_service_id (Union[None, Unset, str]): The PagerDuty service id associated to this team
        opsgenie_id (Union[None, Unset, str]): The Opsgenie group id associated to this team
        victor_ops_id (Union[None, Unset, str]): The VictorOps group id associated to this team
        pagertree_id (Union[None, Unset, str]): The PagerTree group id associated to this team
        cortex_id (Union[None, Unset, str]): The Cortex group id associated to this team
        service_now_ci_sys_id (Union[None, Unset, str]): The Service Now CI sys id associated to this team
        user_ids (Union[None, Unset, list[int]]): The user ids of the members of this team.
        admin_ids (Union[None, Unset, list[int]]): The user ids of the admins of this team. These users must also be
            present in user_ids attribute.
        alerts_email_enabled (Union[None, Unset, bool]): Enable alerts through email
        alert_urgency_id (Union[None, Unset, str]): The alert urgency id of the team
        slack_channels (Union[None, Unset, list['UpdateTeamDataAttributesSlackChannelsType0Item']]): Slack Channels
            associated with this team
        slack_aliases (Union[None, Unset, list['UpdateTeamDataAttributesSlackAliasesType0Item']]): Slack Aliases
            associated with this team
    """

    name: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    notify_emails: Union[None, Unset, list[str]] = UNSET
    color: Union[None, Unset, str] = UNSET
    position: Union[None, Unset, int] = UNSET
    backstage_id: Union[None, Unset, str] = UNSET
    external_id: Union[None, Unset, str] = UNSET
    pagerduty_id: Union[None, Unset, str] = UNSET
    pagerduty_service_id: Union[None, Unset, str] = UNSET
    opsgenie_id: Union[None, Unset, str] = UNSET
    victor_ops_id: Union[None, Unset, str] = UNSET
    pagertree_id: Union[None, Unset, str] = UNSET
    cortex_id: Union[None, Unset, str] = UNSET
    service_now_ci_sys_id: Union[None, Unset, str] = UNSET
    user_ids: Union[None, Unset, list[int]] = UNSET
    admin_ids: Union[None, Unset, list[int]] = UNSET
    alerts_email_enabled: Union[None, Unset, bool] = UNSET
    alert_urgency_id: Union[None, Unset, str] = UNSET
    slack_channels: Union[None, Unset, list["UpdateTeamDataAttributesSlackChannelsType0Item"]] = UNSET
    slack_aliases: Union[None, Unset, list["UpdateTeamDataAttributesSlackAliasesType0Item"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        notify_emails: Union[None, Unset, list[str]]
        if isinstance(self.notify_emails, Unset):
            notify_emails = UNSET
        elif isinstance(self.notify_emails, list):
            notify_emails = self.notify_emails

        else:
            notify_emails = self.notify_emails

        color: Union[None, Unset, str]
        if isinstance(self.color, Unset):
            color = UNSET
        else:
            color = self.color

        position: Union[None, Unset, int]
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        backstage_id: Union[None, Unset, str]
        if isinstance(self.backstage_id, Unset):
            backstage_id = UNSET
        else:
            backstage_id = self.backstage_id

        external_id: Union[None, Unset, str]
        if isinstance(self.external_id, Unset):
            external_id = UNSET
        else:
            external_id = self.external_id

        pagerduty_id: Union[None, Unset, str]
        if isinstance(self.pagerduty_id, Unset):
            pagerduty_id = UNSET
        else:
            pagerduty_id = self.pagerduty_id

        pagerduty_service_id: Union[None, Unset, str]
        if isinstance(self.pagerduty_service_id, Unset):
            pagerduty_service_id = UNSET
        else:
            pagerduty_service_id = self.pagerduty_service_id

        opsgenie_id: Union[None, Unset, str]
        if isinstance(self.opsgenie_id, Unset):
            opsgenie_id = UNSET
        else:
            opsgenie_id = self.opsgenie_id

        victor_ops_id: Union[None, Unset, str]
        if isinstance(self.victor_ops_id, Unset):
            victor_ops_id = UNSET
        else:
            victor_ops_id = self.victor_ops_id

        pagertree_id: Union[None, Unset, str]
        if isinstance(self.pagertree_id, Unset):
            pagertree_id = UNSET
        else:
            pagertree_id = self.pagertree_id

        cortex_id: Union[None, Unset, str]
        if isinstance(self.cortex_id, Unset):
            cortex_id = UNSET
        else:
            cortex_id = self.cortex_id

        service_now_ci_sys_id: Union[None, Unset, str]
        if isinstance(self.service_now_ci_sys_id, Unset):
            service_now_ci_sys_id = UNSET
        else:
            service_now_ci_sys_id = self.service_now_ci_sys_id

        user_ids: Union[None, Unset, list[int]]
        if isinstance(self.user_ids, Unset):
            user_ids = UNSET
        elif isinstance(self.user_ids, list):
            user_ids = self.user_ids

        else:
            user_ids = self.user_ids

        admin_ids: Union[None, Unset, list[int]]
        if isinstance(self.admin_ids, Unset):
            admin_ids = UNSET
        elif isinstance(self.admin_ids, list):
            admin_ids = self.admin_ids

        else:
            admin_ids = self.admin_ids

        alerts_email_enabled: Union[None, Unset, bool]
        if isinstance(self.alerts_email_enabled, Unset):
            alerts_email_enabled = UNSET
        else:
            alerts_email_enabled = self.alerts_email_enabled

        alert_urgency_id: Union[None, Unset, str]
        if isinstance(self.alert_urgency_id, Unset):
            alert_urgency_id = UNSET
        else:
            alert_urgency_id = self.alert_urgency_id

        slack_channels: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.slack_channels, Unset):
            slack_channels = UNSET
        elif isinstance(self.slack_channels, list):
            slack_channels = []
            for slack_channels_type_0_item_data in self.slack_channels:
                slack_channels_type_0_item = slack_channels_type_0_item_data.to_dict()
                slack_channels.append(slack_channels_type_0_item)

        else:
            slack_channels = self.slack_channels

        slack_aliases: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.slack_aliases, Unset):
            slack_aliases = UNSET
        elif isinstance(self.slack_aliases, list):
            slack_aliases = []
            for slack_aliases_type_0_item_data in self.slack_aliases:
                slack_aliases_type_0_item = slack_aliases_type_0_item_data.to_dict()
                slack_aliases.append(slack_aliases_type_0_item)

        else:
            slack_aliases = self.slack_aliases

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if notify_emails is not UNSET:
            field_dict["notify_emails"] = notify_emails
        if color is not UNSET:
            field_dict["color"] = color
        if position is not UNSET:
            field_dict["position"] = position
        if backstage_id is not UNSET:
            field_dict["backstage_id"] = backstage_id
        if external_id is not UNSET:
            field_dict["external_id"] = external_id
        if pagerduty_id is not UNSET:
            field_dict["pagerduty_id"] = pagerduty_id
        if pagerduty_service_id is not UNSET:
            field_dict["pagerduty_service_id"] = pagerduty_service_id
        if opsgenie_id is not UNSET:
            field_dict["opsgenie_id"] = opsgenie_id
        if victor_ops_id is not UNSET:
            field_dict["victor_ops_id"] = victor_ops_id
        if pagertree_id is not UNSET:
            field_dict["pagertree_id"] = pagertree_id
        if cortex_id is not UNSET:
            field_dict["cortex_id"] = cortex_id
        if service_now_ci_sys_id is not UNSET:
            field_dict["service_now_ci_sys_id"] = service_now_ci_sys_id
        if user_ids is not UNSET:
            field_dict["user_ids"] = user_ids
        if admin_ids is not UNSET:
            field_dict["admin_ids"] = admin_ids
        if alerts_email_enabled is not UNSET:
            field_dict["alerts_email_enabled"] = alerts_email_enabled
        if alert_urgency_id is not UNSET:
            field_dict["alert_urgency_id"] = alert_urgency_id
        if slack_channels is not UNSET:
            field_dict["slack_channels"] = slack_channels
        if slack_aliases is not UNSET:
            field_dict["slack_aliases"] = slack_aliases

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.update_team_data_attributes_slack_aliases_type_0_item import (
            UpdateTeamDataAttributesSlackAliasesType0Item,
        )
        from ..models.update_team_data_attributes_slack_channels_type_0_item import (
            UpdateTeamDataAttributesSlackChannelsType0Item,
        )

        d = src_dict.copy()
        name = d.pop("name", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_notify_emails(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                notify_emails_type_0 = cast(list[str], data)

                return notify_emails_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        notify_emails = _parse_notify_emails(d.pop("notify_emails", UNSET))

        def _parse_color(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        color = _parse_color(d.pop("color", UNSET))

        def _parse_position(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        position = _parse_position(d.pop("position", UNSET))

        def _parse_backstage_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        backstage_id = _parse_backstage_id(d.pop("backstage_id", UNSET))

        def _parse_external_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_id = _parse_external_id(d.pop("external_id", UNSET))

        def _parse_pagerduty_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        pagerduty_id = _parse_pagerduty_id(d.pop("pagerduty_id", UNSET))

        def _parse_pagerduty_service_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        pagerduty_service_id = _parse_pagerduty_service_id(d.pop("pagerduty_service_id", UNSET))

        def _parse_opsgenie_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        opsgenie_id = _parse_opsgenie_id(d.pop("opsgenie_id", UNSET))

        def _parse_victor_ops_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        victor_ops_id = _parse_victor_ops_id(d.pop("victor_ops_id", UNSET))

        def _parse_pagertree_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        pagertree_id = _parse_pagertree_id(d.pop("pagertree_id", UNSET))

        def _parse_cortex_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        cortex_id = _parse_cortex_id(d.pop("cortex_id", UNSET))

        def _parse_service_now_ci_sys_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        service_now_ci_sys_id = _parse_service_now_ci_sys_id(d.pop("service_now_ci_sys_id", UNSET))

        def _parse_user_ids(data: object) -> Union[None, Unset, list[int]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                user_ids_type_0 = cast(list[int], data)

                return user_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[int]], data)

        user_ids = _parse_user_ids(d.pop("user_ids", UNSET))

        def _parse_admin_ids(data: object) -> Union[None, Unset, list[int]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                admin_ids_type_0 = cast(list[int], data)

                return admin_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[int]], data)

        admin_ids = _parse_admin_ids(d.pop("admin_ids", UNSET))

        def _parse_alerts_email_enabled(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        alerts_email_enabled = _parse_alerts_email_enabled(d.pop("alerts_email_enabled", UNSET))

        def _parse_alert_urgency_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        alert_urgency_id = _parse_alert_urgency_id(d.pop("alert_urgency_id", UNSET))

        def _parse_slack_channels(
            data: object,
        ) -> Union[None, Unset, list["UpdateTeamDataAttributesSlackChannelsType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                slack_channels_type_0 = []
                _slack_channels_type_0 = data
                for slack_channels_type_0_item_data in _slack_channels_type_0:
                    slack_channels_type_0_item = UpdateTeamDataAttributesSlackChannelsType0Item.from_dict(
                        slack_channels_type_0_item_data
                    )

                    slack_channels_type_0.append(slack_channels_type_0_item)

                return slack_channels_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["UpdateTeamDataAttributesSlackChannelsType0Item"]], data)

        slack_channels = _parse_slack_channels(d.pop("slack_channels", UNSET))

        def _parse_slack_aliases(
            data: object,
        ) -> Union[None, Unset, list["UpdateTeamDataAttributesSlackAliasesType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                slack_aliases_type_0 = []
                _slack_aliases_type_0 = data
                for slack_aliases_type_0_item_data in _slack_aliases_type_0:
                    slack_aliases_type_0_item = UpdateTeamDataAttributesSlackAliasesType0Item.from_dict(
                        slack_aliases_type_0_item_data
                    )

                    slack_aliases_type_0.append(slack_aliases_type_0_item)

                return slack_aliases_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["UpdateTeamDataAttributesSlackAliasesType0Item"]], data)

        slack_aliases = _parse_slack_aliases(d.pop("slack_aliases", UNSET))

        update_team_data_attributes = cls(
            name=name,
            description=description,
            notify_emails=notify_emails,
            color=color,
            position=position,
            backstage_id=backstage_id,
            external_id=external_id,
            pagerduty_id=pagerduty_id,
            pagerduty_service_id=pagerduty_service_id,
            opsgenie_id=opsgenie_id,
            victor_ops_id=victor_ops_id,
            pagertree_id=pagertree_id,
            cortex_id=cortex_id,
            service_now_ci_sys_id=service_now_ci_sys_id,
            user_ids=user_ids,
            admin_ids=admin_ids,
            alerts_email_enabled=alerts_email_enabled,
            alert_urgency_id=alert_urgency_id,
            slack_channels=slack_channels,
            slack_aliases=slack_aliases,
        )

        return update_team_data_attributes
