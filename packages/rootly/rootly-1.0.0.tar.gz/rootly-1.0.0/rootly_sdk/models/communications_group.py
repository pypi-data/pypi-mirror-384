from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.communications_group_condition_type import CommunicationsGroupConditionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.communications_group_communication_external_group_members_type_0_item import (
        CommunicationsGroupCommunicationExternalGroupMembersType0Item,
    )
    from ..models.communications_group_communication_group_conditions_type_0_item import (
        CommunicationsGroupCommunicationGroupConditionsType0Item,
    )
    from ..models.communications_group_communication_group_members_type_0_item import (
        CommunicationsGroupCommunicationGroupMembersType0Item,
    )


T = TypeVar("T", bound="CommunicationsGroup")


@_attrs_define
class CommunicationsGroup:
    """
    Attributes:
        name (str): The name of the communications group
        slug (str): The slug of the communications group
        communication_type_id (str): The communication type ID
        is_private (bool): Whether the group is private
        condition_type (CommunicationsGroupConditionType): Condition type
        sms_channel (bool): SMS channel enabled
        email_channel (bool): Email channel enabled
        created_at (str): Date of creation
        updated_at (str): Date of last update
        description (Union[None, Unset, str]): The description of the communications group
        communication_group_conditions (Union[None, Unset,
            list['CommunicationsGroupCommunicationGroupConditionsType0Item']]): Group conditions
        communication_group_members (Union[None, Unset, list['CommunicationsGroupCommunicationGroupMembersType0Item']]):
            Group members
        communication_external_group_members (Union[None, Unset,
            list['CommunicationsGroupCommunicationExternalGroupMembersType0Item']]): External group members
    """

    name: str
    slug: str
    communication_type_id: str
    is_private: bool
    condition_type: CommunicationsGroupConditionType
    sms_channel: bool
    email_channel: bool
    created_at: str
    updated_at: str
    description: Union[None, Unset, str] = UNSET
    communication_group_conditions: Union[
        None, Unset, list["CommunicationsGroupCommunicationGroupConditionsType0Item"]
    ] = UNSET
    communication_group_members: Union[None, Unset, list["CommunicationsGroupCommunicationGroupMembersType0Item"]] = (
        UNSET
    )
    communication_external_group_members: Union[
        None, Unset, list["CommunicationsGroupCommunicationExternalGroupMembersType0Item"]
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        communication_type_id = self.communication_type_id

        is_private = self.is_private

        condition_type = self.condition_type.value

        sms_channel = self.sms_channel

        email_channel = self.email_channel

        created_at = self.created_at

        updated_at = self.updated_at

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        communication_group_conditions: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.communication_group_conditions, Unset):
            communication_group_conditions = UNSET
        elif isinstance(self.communication_group_conditions, list):
            communication_group_conditions = []
            for communication_group_conditions_type_0_item_data in self.communication_group_conditions:
                communication_group_conditions_type_0_item = communication_group_conditions_type_0_item_data.to_dict()
                communication_group_conditions.append(communication_group_conditions_type_0_item)

        else:
            communication_group_conditions = self.communication_group_conditions

        communication_group_members: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.communication_group_members, Unset):
            communication_group_members = UNSET
        elif isinstance(self.communication_group_members, list):
            communication_group_members = []
            for communication_group_members_type_0_item_data in self.communication_group_members:
                communication_group_members_type_0_item = communication_group_members_type_0_item_data.to_dict()
                communication_group_members.append(communication_group_members_type_0_item)

        else:
            communication_group_members = self.communication_group_members

        communication_external_group_members: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.communication_external_group_members, Unset):
            communication_external_group_members = UNSET
        elif isinstance(self.communication_external_group_members, list):
            communication_external_group_members = []
            for communication_external_group_members_type_0_item_data in self.communication_external_group_members:
                communication_external_group_members_type_0_item = (
                    communication_external_group_members_type_0_item_data.to_dict()
                )
                communication_external_group_members.append(communication_external_group_members_type_0_item)

        else:
            communication_external_group_members = self.communication_external_group_members

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "slug": slug,
                "communication_type_id": communication_type_id,
                "is_private": is_private,
                "condition_type": condition_type,
                "sms_channel": sms_channel,
                "email_channel": email_channel,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if communication_group_conditions is not UNSET:
            field_dict["communication_group_conditions"] = communication_group_conditions
        if communication_group_members is not UNSET:
            field_dict["communication_group_members"] = communication_group_members
        if communication_external_group_members is not UNSET:
            field_dict["communication_external_group_members"] = communication_external_group_members

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.communications_group_communication_external_group_members_type_0_item import (
            CommunicationsGroupCommunicationExternalGroupMembersType0Item,
        )
        from ..models.communications_group_communication_group_conditions_type_0_item import (
            CommunicationsGroupCommunicationGroupConditionsType0Item,
        )
        from ..models.communications_group_communication_group_members_type_0_item import (
            CommunicationsGroupCommunicationGroupMembersType0Item,
        )

        d = src_dict.copy()
        name = d.pop("name")

        slug = d.pop("slug")

        communication_type_id = d.pop("communication_type_id")

        is_private = d.pop("is_private")

        condition_type = CommunicationsGroupConditionType(d.pop("condition_type"))

        sms_channel = d.pop("sms_channel")

        email_channel = d.pop("email_channel")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_communication_group_conditions(
            data: object,
        ) -> Union[None, Unset, list["CommunicationsGroupCommunicationGroupConditionsType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                communication_group_conditions_type_0 = []
                _communication_group_conditions_type_0 = data
                for communication_group_conditions_type_0_item_data in _communication_group_conditions_type_0:
                    communication_group_conditions_type_0_item = (
                        CommunicationsGroupCommunicationGroupConditionsType0Item.from_dict(
                            communication_group_conditions_type_0_item_data
                        )
                    )

                    communication_group_conditions_type_0.append(communication_group_conditions_type_0_item)

                return communication_group_conditions_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["CommunicationsGroupCommunicationGroupConditionsType0Item"]], data)

        communication_group_conditions = _parse_communication_group_conditions(
            d.pop("communication_group_conditions", UNSET)
        )

        def _parse_communication_group_members(
            data: object,
        ) -> Union[None, Unset, list["CommunicationsGroupCommunicationGroupMembersType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                communication_group_members_type_0 = []
                _communication_group_members_type_0 = data
                for communication_group_members_type_0_item_data in _communication_group_members_type_0:
                    communication_group_members_type_0_item = (
                        CommunicationsGroupCommunicationGroupMembersType0Item.from_dict(
                            communication_group_members_type_0_item_data
                        )
                    )

                    communication_group_members_type_0.append(communication_group_members_type_0_item)

                return communication_group_members_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["CommunicationsGroupCommunicationGroupMembersType0Item"]], data)

        communication_group_members = _parse_communication_group_members(d.pop("communication_group_members", UNSET))

        def _parse_communication_external_group_members(
            data: object,
        ) -> Union[None, Unset, list["CommunicationsGroupCommunicationExternalGroupMembersType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                communication_external_group_members_type_0 = []
                _communication_external_group_members_type_0 = data
                for (
                    communication_external_group_members_type_0_item_data
                ) in _communication_external_group_members_type_0:
                    communication_external_group_members_type_0_item = (
                        CommunicationsGroupCommunicationExternalGroupMembersType0Item.from_dict(
                            communication_external_group_members_type_0_item_data
                        )
                    )

                    communication_external_group_members_type_0.append(communication_external_group_members_type_0_item)

                return communication_external_group_members_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["CommunicationsGroupCommunicationExternalGroupMembersType0Item"]], data)

        communication_external_group_members = _parse_communication_external_group_members(
            d.pop("communication_external_group_members", UNSET)
        )

        communications_group = cls(
            name=name,
            slug=slug,
            communication_type_id=communication_type_id,
            is_private=is_private,
            condition_type=condition_type,
            sms_channel=sms_channel,
            email_channel=email_channel,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            communication_group_conditions=communication_group_conditions,
            communication_group_members=communication_group_members,
            communication_external_group_members=communication_external_group_members,
        )

        communications_group.additional_properties = d
        return communications_group

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
