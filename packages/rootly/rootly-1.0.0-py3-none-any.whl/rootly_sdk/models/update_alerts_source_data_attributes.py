from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_alerts_source_data_attributes_source_type import UpdateAlertsSourceDataAttributesSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_alerts_source_data_attributes_alert_source_fields_attributes_item import (
        UpdateAlertsSourceDataAttributesAlertSourceFieldsAttributesItem,
    )
    from ..models.update_alerts_source_data_attributes_alert_source_urgency_rules_attributes_item import (
        UpdateAlertsSourceDataAttributesAlertSourceUrgencyRulesAttributesItem,
    )
    from ..models.update_alerts_source_data_attributes_alert_template_attributes import (
        UpdateAlertsSourceDataAttributesAlertTemplateAttributes,
    )
    from ..models.update_alerts_source_data_attributes_resolution_rule_attributes import (
        UpdateAlertsSourceDataAttributesResolutionRuleAttributes,
    )
    from ..models.update_alerts_source_data_attributes_sourceable_attributes import (
        UpdateAlertsSourceDataAttributesSourceableAttributes,
    )


T = TypeVar("T", bound="UpdateAlertsSourceDataAttributes")


@_attrs_define
class UpdateAlertsSourceDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]): The name of the alert source
        source_type (Union[Unset, UpdateAlertsSourceDataAttributesSourceType]): The alert source type
        alert_urgency_id (Union[Unset, str]): ID for the default alert urgency assigned to this alert source
        owner_group_ids (Union[Unset, list[str]]): List of team IDs that will own the alert source
        alert_template_attributes (Union[Unset, UpdateAlertsSourceDataAttributesAlertTemplateAttributes]):
        alert_source_urgency_rules_attributes (Union[Unset,
            list['UpdateAlertsSourceDataAttributesAlertSourceUrgencyRulesAttributesItem']]): List of rules that define the
            conditions under which the alert urgency will be set automatically based on the alert payload
        sourceable_attributes (Union[Unset, UpdateAlertsSourceDataAttributesSourceableAttributes]): Provide additional
            attributes for generic_webhook alerts source
        resolution_rule_attributes (Union[Unset, UpdateAlertsSourceDataAttributesResolutionRuleAttributes]): Provide
            additional attributes for email alerts source
        alert_source_fields_attributes (Union[Unset,
            list['UpdateAlertsSourceDataAttributesAlertSourceFieldsAttributesItem']]): List of alert fields to be added to
            the alert source
    """

    name: Union[Unset, str] = UNSET
    source_type: Union[Unset, UpdateAlertsSourceDataAttributesSourceType] = UNSET
    alert_urgency_id: Union[Unset, str] = UNSET
    owner_group_ids: Union[Unset, list[str]] = UNSET
    alert_template_attributes: Union[Unset, "UpdateAlertsSourceDataAttributesAlertTemplateAttributes"] = UNSET
    alert_source_urgency_rules_attributes: Union[
        Unset, list["UpdateAlertsSourceDataAttributesAlertSourceUrgencyRulesAttributesItem"]
    ] = UNSET
    sourceable_attributes: Union[Unset, "UpdateAlertsSourceDataAttributesSourceableAttributes"] = UNSET
    resolution_rule_attributes: Union[Unset, "UpdateAlertsSourceDataAttributesResolutionRuleAttributes"] = UNSET
    alert_source_fields_attributes: Union[
        Unset, list["UpdateAlertsSourceDataAttributesAlertSourceFieldsAttributesItem"]
    ] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        source_type: Union[Unset, str] = UNSET
        if not isinstance(self.source_type, Unset):
            source_type = self.source_type.value

        alert_urgency_id = self.alert_urgency_id

        owner_group_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.owner_group_ids, Unset):
            owner_group_ids = self.owner_group_ids

        alert_template_attributes: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.alert_template_attributes, Unset):
            alert_template_attributes = self.alert_template_attributes.to_dict()

        alert_source_urgency_rules_attributes: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.alert_source_urgency_rules_attributes, Unset):
            alert_source_urgency_rules_attributes = []
            for alert_source_urgency_rules_attributes_item_data in self.alert_source_urgency_rules_attributes:
                alert_source_urgency_rules_attributes_item = alert_source_urgency_rules_attributes_item_data.to_dict()
                alert_source_urgency_rules_attributes.append(alert_source_urgency_rules_attributes_item)

        sourceable_attributes: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.sourceable_attributes, Unset):
            sourceable_attributes = self.sourceable_attributes.to_dict()

        resolution_rule_attributes: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.resolution_rule_attributes, Unset):
            resolution_rule_attributes = self.resolution_rule_attributes.to_dict()

        alert_source_fields_attributes: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.alert_source_fields_attributes, Unset):
            alert_source_fields_attributes = []
            for alert_source_fields_attributes_item_data in self.alert_source_fields_attributes:
                alert_source_fields_attributes_item = alert_source_fields_attributes_item_data.to_dict()
                alert_source_fields_attributes.append(alert_source_fields_attributes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if alert_urgency_id is not UNSET:
            field_dict["alert_urgency_id"] = alert_urgency_id
        if owner_group_ids is not UNSET:
            field_dict["owner_group_ids"] = owner_group_ids
        if alert_template_attributes is not UNSET:
            field_dict["alert_template_attributes"] = alert_template_attributes
        if alert_source_urgency_rules_attributes is not UNSET:
            field_dict["alert_source_urgency_rules_attributes"] = alert_source_urgency_rules_attributes
        if sourceable_attributes is not UNSET:
            field_dict["sourceable_attributes"] = sourceable_attributes
        if resolution_rule_attributes is not UNSET:
            field_dict["resolution_rule_attributes"] = resolution_rule_attributes
        if alert_source_fields_attributes is not UNSET:
            field_dict["alert_source_fields_attributes"] = alert_source_fields_attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.update_alerts_source_data_attributes_alert_source_fields_attributes_item import (
            UpdateAlertsSourceDataAttributesAlertSourceFieldsAttributesItem,
        )
        from ..models.update_alerts_source_data_attributes_alert_source_urgency_rules_attributes_item import (
            UpdateAlertsSourceDataAttributesAlertSourceUrgencyRulesAttributesItem,
        )
        from ..models.update_alerts_source_data_attributes_alert_template_attributes import (
            UpdateAlertsSourceDataAttributesAlertTemplateAttributes,
        )
        from ..models.update_alerts_source_data_attributes_resolution_rule_attributes import (
            UpdateAlertsSourceDataAttributesResolutionRuleAttributes,
        )
        from ..models.update_alerts_source_data_attributes_sourceable_attributes import (
            UpdateAlertsSourceDataAttributesSourceableAttributes,
        )

        d = src_dict.copy()
        name = d.pop("name", UNSET)

        _source_type = d.pop("source_type", UNSET)
        source_type: Union[Unset, UpdateAlertsSourceDataAttributesSourceType]
        if isinstance(_source_type, Unset):
            source_type = UNSET
        else:
            source_type = UpdateAlertsSourceDataAttributesSourceType(_source_type)

        alert_urgency_id = d.pop("alert_urgency_id", UNSET)

        owner_group_ids = cast(list[str], d.pop("owner_group_ids", UNSET))

        _alert_template_attributes = d.pop("alert_template_attributes", UNSET)
        alert_template_attributes: Union[Unset, UpdateAlertsSourceDataAttributesAlertTemplateAttributes]
        if isinstance(_alert_template_attributes, Unset):
            alert_template_attributes = UNSET
        else:
            alert_template_attributes = UpdateAlertsSourceDataAttributesAlertTemplateAttributes.from_dict(
                _alert_template_attributes
            )

        alert_source_urgency_rules_attributes = []
        _alert_source_urgency_rules_attributes = d.pop("alert_source_urgency_rules_attributes", UNSET)
        for alert_source_urgency_rules_attributes_item_data in _alert_source_urgency_rules_attributes or []:
            alert_source_urgency_rules_attributes_item = (
                UpdateAlertsSourceDataAttributesAlertSourceUrgencyRulesAttributesItem.from_dict(
                    alert_source_urgency_rules_attributes_item_data
                )
            )

            alert_source_urgency_rules_attributes.append(alert_source_urgency_rules_attributes_item)

        _sourceable_attributes = d.pop("sourceable_attributes", UNSET)
        sourceable_attributes: Union[Unset, UpdateAlertsSourceDataAttributesSourceableAttributes]
        if isinstance(_sourceable_attributes, Unset):
            sourceable_attributes = UNSET
        else:
            sourceable_attributes = UpdateAlertsSourceDataAttributesSourceableAttributes.from_dict(
                _sourceable_attributes
            )

        _resolution_rule_attributes = d.pop("resolution_rule_attributes", UNSET)
        resolution_rule_attributes: Union[Unset, UpdateAlertsSourceDataAttributesResolutionRuleAttributes]
        if isinstance(_resolution_rule_attributes, Unset):
            resolution_rule_attributes = UNSET
        else:
            resolution_rule_attributes = UpdateAlertsSourceDataAttributesResolutionRuleAttributes.from_dict(
                _resolution_rule_attributes
            )

        alert_source_fields_attributes = []
        _alert_source_fields_attributes = d.pop("alert_source_fields_attributes", UNSET)
        for alert_source_fields_attributes_item_data in _alert_source_fields_attributes or []:
            alert_source_fields_attributes_item = (
                UpdateAlertsSourceDataAttributesAlertSourceFieldsAttributesItem.from_dict(
                    alert_source_fields_attributes_item_data
                )
            )

            alert_source_fields_attributes.append(alert_source_fields_attributes_item)

        update_alerts_source_data_attributes = cls(
            name=name,
            source_type=source_type,
            alert_urgency_id=alert_urgency_id,
            owner_group_ids=owner_group_ids,
            alert_template_attributes=alert_template_attributes,
            alert_source_urgency_rules_attributes=alert_source_urgency_rules_attributes,
            sourceable_attributes=sourceable_attributes,
            resolution_rule_attributes=resolution_rule_attributes,
            alert_source_fields_attributes=alert_source_fields_attributes,
        )

        return update_alerts_source_data_attributes
