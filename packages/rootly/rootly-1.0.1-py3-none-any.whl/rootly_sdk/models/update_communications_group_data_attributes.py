from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_communications_group_data_attributes_condition_type import (
    UpdateCommunicationsGroupDataAttributesConditionType,
    check_update_communications_group_data_attributes_condition_type,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_communications_group_data_attributes_communication_external_group_members_attributes_type_0_item import (
        UpdateCommunicationsGroupDataAttributesCommunicationExternalGroupMembersAttributesType0Item,
    )
    from ..models.update_communications_group_data_attributes_communication_group_conditions_attributes_type_0_item import (
        UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0Item,
    )
    from ..models.update_communications_group_data_attributes_communication_group_members_attributes_type_0_item import (
        UpdateCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item,
    )


T = TypeVar("T", bound="UpdateCommunicationsGroupDataAttributes")


@_attrs_define
class UpdateCommunicationsGroupDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]): The name of the communications group
        description (Union[None, Unset, str]): The description of the communications group
        communication_type_id (Union[Unset, str]): The communication type ID
        is_private (Union[None, Unset, bool]): Whether the group is private
        condition_type (Union[Unset, UpdateCommunicationsGroupDataAttributesConditionType]): Condition type
        sms_channel (Union[None, Unset, bool]): SMS channel enabled
        email_channel (Union[None, Unset, bool]): Email channel enabled
        slack_channel_ids (Union[None, Unset, list[str]]): Array of Slack channel IDs
        communication_group_conditions_attributes (Union[None, Unset,
            list['UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0Item']]): Group
            conditions attributes
        communication_group_members_attributes (Union[None, Unset,
            list['UpdateCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item']]): Group members
            attributes
        communication_external_group_members_attributes (Union[None, Unset,
            list['UpdateCommunicationsGroupDataAttributesCommunicationExternalGroupMembersAttributesType0Item']]): External
            group members attributes
    """

    name: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    communication_type_id: Union[Unset, str] = UNSET
    is_private: Union[None, Unset, bool] = UNSET
    condition_type: Union[Unset, UpdateCommunicationsGroupDataAttributesConditionType] = UNSET
    sms_channel: Union[None, Unset, bool] = UNSET
    email_channel: Union[None, Unset, bool] = UNSET
    slack_channel_ids: Union[None, Unset, list[str]] = UNSET
    communication_group_conditions_attributes: Union[
        None, Unset, list["UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0Item"]
    ] = UNSET
    communication_group_members_attributes: Union[
        None, Unset, list["UpdateCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item"]
    ] = UNSET
    communication_external_group_members_attributes: Union[
        None, Unset, list["UpdateCommunicationsGroupDataAttributesCommunicationExternalGroupMembersAttributesType0Item"]
    ] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        communication_type_id = self.communication_type_id

        is_private: Union[None, Unset, bool]
        if isinstance(self.is_private, Unset):
            is_private = UNSET
        else:
            is_private = self.is_private

        condition_type: Union[Unset, str] = UNSET
        if not isinstance(self.condition_type, Unset):
            condition_type = self.condition_type

        sms_channel: Union[None, Unset, bool]
        if isinstance(self.sms_channel, Unset):
            sms_channel = UNSET
        else:
            sms_channel = self.sms_channel

        email_channel: Union[None, Unset, bool]
        if isinstance(self.email_channel, Unset):
            email_channel = UNSET
        else:
            email_channel = self.email_channel

        slack_channel_ids: Union[None, Unset, list[str]]
        if isinstance(self.slack_channel_ids, Unset):
            slack_channel_ids = UNSET
        elif isinstance(self.slack_channel_ids, list):
            slack_channel_ids = self.slack_channel_ids

        else:
            slack_channel_ids = self.slack_channel_ids

        communication_group_conditions_attributes: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.communication_group_conditions_attributes, Unset):
            communication_group_conditions_attributes = UNSET
        elif isinstance(self.communication_group_conditions_attributes, list):
            communication_group_conditions_attributes = []
            for (
                communication_group_conditions_attributes_type_0_item_data
            ) in self.communication_group_conditions_attributes:
                communication_group_conditions_attributes_type_0_item = (
                    communication_group_conditions_attributes_type_0_item_data.to_dict()
                )
                communication_group_conditions_attributes.append(communication_group_conditions_attributes_type_0_item)

        else:
            communication_group_conditions_attributes = self.communication_group_conditions_attributes

        communication_group_members_attributes: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.communication_group_members_attributes, Unset):
            communication_group_members_attributes = UNSET
        elif isinstance(self.communication_group_members_attributes, list):
            communication_group_members_attributes = []
            for communication_group_members_attributes_type_0_item_data in self.communication_group_members_attributes:
                communication_group_members_attributes_type_0_item = (
                    communication_group_members_attributes_type_0_item_data.to_dict()
                )
                communication_group_members_attributes.append(communication_group_members_attributes_type_0_item)

        else:
            communication_group_members_attributes = self.communication_group_members_attributes

        communication_external_group_members_attributes: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.communication_external_group_members_attributes, Unset):
            communication_external_group_members_attributes = UNSET
        elif isinstance(self.communication_external_group_members_attributes, list):
            communication_external_group_members_attributes = []
            for (
                communication_external_group_members_attributes_type_0_item_data
            ) in self.communication_external_group_members_attributes:
                communication_external_group_members_attributes_type_0_item = (
                    communication_external_group_members_attributes_type_0_item_data.to_dict()
                )
                communication_external_group_members_attributes.append(
                    communication_external_group_members_attributes_type_0_item
                )

        else:
            communication_external_group_members_attributes = self.communication_external_group_members_attributes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if communication_type_id is not UNSET:
            field_dict["communication_type_id"] = communication_type_id
        if is_private is not UNSET:
            field_dict["is_private"] = is_private
        if condition_type is not UNSET:
            field_dict["condition_type"] = condition_type
        if sms_channel is not UNSET:
            field_dict["sms_channel"] = sms_channel
        if email_channel is not UNSET:
            field_dict["email_channel"] = email_channel
        if slack_channel_ids is not UNSET:
            field_dict["slack_channel_ids"] = slack_channel_ids
        if communication_group_conditions_attributes is not UNSET:
            field_dict["communication_group_conditions_attributes"] = communication_group_conditions_attributes
        if communication_group_members_attributes is not UNSET:
            field_dict["communication_group_members_attributes"] = communication_group_members_attributes
        if communication_external_group_members_attributes is not UNSET:
            field_dict["communication_external_group_members_attributes"] = (
                communication_external_group_members_attributes
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_communications_group_data_attributes_communication_external_group_members_attributes_type_0_item import (
            UpdateCommunicationsGroupDataAttributesCommunicationExternalGroupMembersAttributesType0Item,
        )
        from ..models.update_communications_group_data_attributes_communication_group_conditions_attributes_type_0_item import (
            UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0Item,
        )
        from ..models.update_communications_group_data_attributes_communication_group_members_attributes_type_0_item import (
            UpdateCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item,
        )

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        communication_type_id = d.pop("communication_type_id", UNSET)

        def _parse_is_private(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        is_private = _parse_is_private(d.pop("is_private", UNSET))

        _condition_type = d.pop("condition_type", UNSET)
        condition_type: Union[Unset, UpdateCommunicationsGroupDataAttributesConditionType]
        if isinstance(_condition_type, Unset):
            condition_type = UNSET
        else:
            condition_type = check_update_communications_group_data_attributes_condition_type(_condition_type)

        def _parse_sms_channel(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        sms_channel = _parse_sms_channel(d.pop("sms_channel", UNSET))

        def _parse_email_channel(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        email_channel = _parse_email_channel(d.pop("email_channel", UNSET))

        def _parse_slack_channel_ids(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                slack_channel_ids_type_0 = cast(list[str], data)

                return slack_channel_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        slack_channel_ids = _parse_slack_channel_ids(d.pop("slack_channel_ids", UNSET))

        def _parse_communication_group_conditions_attributes(
            data: object,
        ) -> Union[
            None, Unset, list["UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0Item"]
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                communication_group_conditions_attributes_type_0 = []
                _communication_group_conditions_attributes_type_0 = data
                for (
                    communication_group_conditions_attributes_type_0_item_data
                ) in _communication_group_conditions_attributes_type_0:
                    communication_group_conditions_attributes_type_0_item = UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0Item.from_dict(
                        communication_group_conditions_attributes_type_0_item_data
                    )

                    communication_group_conditions_attributes_type_0.append(
                        communication_group_conditions_attributes_type_0_item
                    )

                return communication_group_conditions_attributes_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    None,
                    Unset,
                    list["UpdateCommunicationsGroupDataAttributesCommunicationGroupConditionsAttributesType0Item"],
                ],
                data,
            )

        communication_group_conditions_attributes = _parse_communication_group_conditions_attributes(
            d.pop("communication_group_conditions_attributes", UNSET)
        )

        def _parse_communication_group_members_attributes(
            data: object,
        ) -> Union[
            None, Unset, list["UpdateCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item"]
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                communication_group_members_attributes_type_0 = []
                _communication_group_members_attributes_type_0 = data
                for (
                    communication_group_members_attributes_type_0_item_data
                ) in _communication_group_members_attributes_type_0:
                    communication_group_members_attributes_type_0_item = (
                        UpdateCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item.from_dict(
                            communication_group_members_attributes_type_0_item_data
                        )
                    )

                    communication_group_members_attributes_type_0.append(
                        communication_group_members_attributes_type_0_item
                    )

                return communication_group_members_attributes_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    None,
                    Unset,
                    list["UpdateCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item"],
                ],
                data,
            )

        communication_group_members_attributes = _parse_communication_group_members_attributes(
            d.pop("communication_group_members_attributes", UNSET)
        )

        def _parse_communication_external_group_members_attributes(
            data: object,
        ) -> Union[
            None,
            Unset,
            list["UpdateCommunicationsGroupDataAttributesCommunicationExternalGroupMembersAttributesType0Item"],
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                communication_external_group_members_attributes_type_0 = []
                _communication_external_group_members_attributes_type_0 = data
                for (
                    communication_external_group_members_attributes_type_0_item_data
                ) in _communication_external_group_members_attributes_type_0:
                    communication_external_group_members_attributes_type_0_item = UpdateCommunicationsGroupDataAttributesCommunicationExternalGroupMembersAttributesType0Item.from_dict(
                        communication_external_group_members_attributes_type_0_item_data
                    )

                    communication_external_group_members_attributes_type_0.append(
                        communication_external_group_members_attributes_type_0_item
                    )

                return communication_external_group_members_attributes_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    None,
                    Unset,
                    list["UpdateCommunicationsGroupDataAttributesCommunicationExternalGroupMembersAttributesType0Item"],
                ],
                data,
            )

        communication_external_group_members_attributes = _parse_communication_external_group_members_attributes(
            d.pop("communication_external_group_members_attributes", UNSET)
        )

        update_communications_group_data_attributes = cls(
            name=name,
            description=description,
            communication_type_id=communication_type_id,
            is_private=is_private,
            condition_type=condition_type,
            sms_channel=sms_channel,
            email_channel=email_channel,
            slack_channel_ids=slack_channel_ids,
            communication_group_conditions_attributes=communication_group_conditions_attributes,
            communication_group_members_attributes=communication_group_members_attributes,
            communication_external_group_members_attributes=communication_external_group_members_attributes,
        )

        return update_communications_group_data_attributes
