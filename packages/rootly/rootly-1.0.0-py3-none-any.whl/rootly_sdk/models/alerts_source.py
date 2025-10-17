from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.alerts_source_source_type import AlertsSourceSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alerts_source_alert_source_fields_attributes_type_0_item import (
        AlertsSourceAlertSourceFieldsAttributesType0Item,
    )
    from ..models.alerts_source_resolution_rule_attributes_type_0 import AlertsSourceResolutionRuleAttributesType0
    from ..models.alerts_source_sourceable_attributes_type_0 import AlertsSourceSourceableAttributesType0


T = TypeVar("T", bound="AlertsSource")


@_attrs_define
class AlertsSource:
    """
    Attributes:
        name (str): The name of the alert source
        status (str): The current status of the alert source
        secret (str): A secret key used to authenticate incoming requests to this alerts source
        created_at (str): Date of creation
        updated_at (str): Date of last update
        alert_urgency_id (Union[Unset, str]): ID for the default alert urgency assigned to this alert source
        source_type (Union[Unset, AlertsSourceSourceType]): The alert source type
        webhook_endpoint (Union[None, Unset, str]): The URL endpoint of the alert source
        email (Union[None, Unset, str]): The email address of the alert source
        owner_group_ids (Union[Unset, list[str]]): List of team IDs that will own the alert source
        sourceable_attributes (Union['AlertsSourceSourceableAttributesType0', None, Unset]): Additional attributes
            specific to certain alert sources (e.g., generic_webhook), encapsulating source-specific configurations or
            details
        resolution_rule_attributes (Union['AlertsSourceResolutionRuleAttributesType0', None, Unset]): Additional
            attributes for email or generic webhook alerts source
        alert_source_fields_attributes (Union[None, Unset, list['AlertsSourceAlertSourceFieldsAttributesType0Item']]):
            List of alert fields to be added to alert source
    """

    name: str
    status: str
    secret: str
    created_at: str
    updated_at: str
    alert_urgency_id: Union[Unset, str] = UNSET
    source_type: Union[Unset, AlertsSourceSourceType] = UNSET
    webhook_endpoint: Union[None, Unset, str] = UNSET
    email: Union[None, Unset, str] = UNSET
    owner_group_ids: Union[Unset, list[str]] = UNSET
    sourceable_attributes: Union["AlertsSourceSourceableAttributesType0", None, Unset] = UNSET
    resolution_rule_attributes: Union["AlertsSourceResolutionRuleAttributesType0", None, Unset] = UNSET
    alert_source_fields_attributes: Union[None, Unset, list["AlertsSourceAlertSourceFieldsAttributesType0Item"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.alerts_source_resolution_rule_attributes_type_0 import AlertsSourceResolutionRuleAttributesType0
        from ..models.alerts_source_sourceable_attributes_type_0 import AlertsSourceSourceableAttributesType0

        name = self.name

        status = self.status

        secret = self.secret

        created_at = self.created_at

        updated_at = self.updated_at

        alert_urgency_id = self.alert_urgency_id

        source_type: Union[Unset, str] = UNSET
        if not isinstance(self.source_type, Unset):
            source_type = self.source_type.value

        webhook_endpoint: Union[None, Unset, str]
        if isinstance(self.webhook_endpoint, Unset):
            webhook_endpoint = UNSET
        else:
            webhook_endpoint = self.webhook_endpoint

        email: Union[None, Unset, str]
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        owner_group_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.owner_group_ids, Unset):
            owner_group_ids = self.owner_group_ids

        sourceable_attributes: Union[None, Unset, dict[str, Any]]
        if isinstance(self.sourceable_attributes, Unset):
            sourceable_attributes = UNSET
        elif isinstance(self.sourceable_attributes, AlertsSourceSourceableAttributesType0):
            sourceable_attributes = self.sourceable_attributes.to_dict()
        else:
            sourceable_attributes = self.sourceable_attributes

        resolution_rule_attributes: Union[None, Unset, dict[str, Any]]
        if isinstance(self.resolution_rule_attributes, Unset):
            resolution_rule_attributes = UNSET
        elif isinstance(self.resolution_rule_attributes, AlertsSourceResolutionRuleAttributesType0):
            resolution_rule_attributes = self.resolution_rule_attributes.to_dict()
        else:
            resolution_rule_attributes = self.resolution_rule_attributes

        alert_source_fields_attributes: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.alert_source_fields_attributes, Unset):
            alert_source_fields_attributes = UNSET
        elif isinstance(self.alert_source_fields_attributes, list):
            alert_source_fields_attributes = []
            for alert_source_fields_attributes_type_0_item_data in self.alert_source_fields_attributes:
                alert_source_fields_attributes_type_0_item = alert_source_fields_attributes_type_0_item_data.to_dict()
                alert_source_fields_attributes.append(alert_source_fields_attributes_type_0_item)

        else:
            alert_source_fields_attributes = self.alert_source_fields_attributes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "status": status,
                "secret": secret,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if alert_urgency_id is not UNSET:
            field_dict["alert_urgency_id"] = alert_urgency_id
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if webhook_endpoint is not UNSET:
            field_dict["webhook_endpoint"] = webhook_endpoint
        if email is not UNSET:
            field_dict["email"] = email
        if owner_group_ids is not UNSET:
            field_dict["owner_group_ids"] = owner_group_ids
        if sourceable_attributes is not UNSET:
            field_dict["sourceable_attributes"] = sourceable_attributes
        if resolution_rule_attributes is not UNSET:
            field_dict["resolution_rule_attributes"] = resolution_rule_attributes
        if alert_source_fields_attributes is not UNSET:
            field_dict["alert_source_fields_attributes"] = alert_source_fields_attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.alerts_source_alert_source_fields_attributes_type_0_item import (
            AlertsSourceAlertSourceFieldsAttributesType0Item,
        )
        from ..models.alerts_source_resolution_rule_attributes_type_0 import AlertsSourceResolutionRuleAttributesType0
        from ..models.alerts_source_sourceable_attributes_type_0 import AlertsSourceSourceableAttributesType0

        d = src_dict.copy()
        name = d.pop("name")

        status = d.pop("status")

        secret = d.pop("secret")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        alert_urgency_id = d.pop("alert_urgency_id", UNSET)

        _source_type = d.pop("source_type", UNSET)
        source_type: Union[Unset, AlertsSourceSourceType]
        if isinstance(_source_type, Unset):
            source_type = UNSET
        else:
            source_type = AlertsSourceSourceType(_source_type)

        def _parse_webhook_endpoint(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        webhook_endpoint = _parse_webhook_endpoint(d.pop("webhook_endpoint", UNSET))

        def _parse_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        email = _parse_email(d.pop("email", UNSET))

        owner_group_ids = cast(list[str], d.pop("owner_group_ids", UNSET))

        def _parse_sourceable_attributes(data: object) -> Union["AlertsSourceSourceableAttributesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                sourceable_attributes_type_0 = AlertsSourceSourceableAttributesType0.from_dict(data)

                return sourceable_attributes_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AlertsSourceSourceableAttributesType0", None, Unset], data)

        sourceable_attributes = _parse_sourceable_attributes(d.pop("sourceable_attributes", UNSET))

        def _parse_resolution_rule_attributes(
            data: object,
        ) -> Union["AlertsSourceResolutionRuleAttributesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                resolution_rule_attributes_type_0 = AlertsSourceResolutionRuleAttributesType0.from_dict(data)

                return resolution_rule_attributes_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AlertsSourceResolutionRuleAttributesType0", None, Unset], data)

        resolution_rule_attributes = _parse_resolution_rule_attributes(d.pop("resolution_rule_attributes", UNSET))

        def _parse_alert_source_fields_attributes(
            data: object,
        ) -> Union[None, Unset, list["AlertsSourceAlertSourceFieldsAttributesType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                alert_source_fields_attributes_type_0 = []
                _alert_source_fields_attributes_type_0 = data
                for alert_source_fields_attributes_type_0_item_data in _alert_source_fields_attributes_type_0:
                    alert_source_fields_attributes_type_0_item = (
                        AlertsSourceAlertSourceFieldsAttributesType0Item.from_dict(
                            alert_source_fields_attributes_type_0_item_data
                        )
                    )

                    alert_source_fields_attributes_type_0.append(alert_source_fields_attributes_type_0_item)

                return alert_source_fields_attributes_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["AlertsSourceAlertSourceFieldsAttributesType0Item"]], data)

        alert_source_fields_attributes = _parse_alert_source_fields_attributes(
            d.pop("alert_source_fields_attributes", UNSET)
        )

        alerts_source = cls(
            name=name,
            status=status,
            secret=secret,
            created_at=created_at,
            updated_at=updated_at,
            alert_urgency_id=alert_urgency_id,
            source_type=source_type,
            webhook_endpoint=webhook_endpoint,
            email=email,
            owner_group_ids=owner_group_ids,
            sourceable_attributes=sourceable_attributes,
            resolution_rule_attributes=resolution_rule_attributes,
            alert_source_fields_attributes=alert_source_fields_attributes,
        )

        alerts_source.additional_properties = d
        return alerts_source

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
