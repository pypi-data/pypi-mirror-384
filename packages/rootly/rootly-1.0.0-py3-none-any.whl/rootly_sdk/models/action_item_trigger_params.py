from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.action_item_trigger_params_incident_action_item_condition import (
    ActionItemTriggerParamsIncidentActionItemCondition,
)
from ..models.action_item_trigger_params_incident_action_item_condition_group import (
    ActionItemTriggerParamsIncidentActionItemConditionGroup,
)
from ..models.action_item_trigger_params_incident_action_item_condition_kind import (
    ActionItemTriggerParamsIncidentActionItemConditionKind,
)
from ..models.action_item_trigger_params_incident_action_item_condition_priority import (
    ActionItemTriggerParamsIncidentActionItemConditionPriority,
)
from ..models.action_item_trigger_params_incident_action_item_condition_status import (
    ActionItemTriggerParamsIncidentActionItemConditionStatus,
)
from ..models.action_item_trigger_params_incident_action_item_kinds_item import (
    ActionItemTriggerParamsIncidentActionItemKindsItem,
)
from ..models.action_item_trigger_params_incident_action_item_priorities_item import (
    ActionItemTriggerParamsIncidentActionItemPrioritiesItem,
)
from ..models.action_item_trigger_params_incident_action_item_statuses_item import (
    ActionItemTriggerParamsIncidentActionItemStatusesItem,
)
from ..models.action_item_trigger_params_incident_condition import ActionItemTriggerParamsIncidentCondition
from ..models.action_item_trigger_params_incident_condition_acknowledged_at_type_1 import (
    ActionItemTriggerParamsIncidentConditionAcknowledgedAtType1,
)
from ..models.action_item_trigger_params_incident_condition_detected_at_type_1 import (
    ActionItemTriggerParamsIncidentConditionDetectedAtType1,
)
from ..models.action_item_trigger_params_incident_condition_environment import (
    ActionItemTriggerParamsIncidentConditionEnvironment,
)
from ..models.action_item_trigger_params_incident_condition_functionality import (
    ActionItemTriggerParamsIncidentConditionFunctionality,
)
from ..models.action_item_trigger_params_incident_condition_group import ActionItemTriggerParamsIncidentConditionGroup
from ..models.action_item_trigger_params_incident_condition_incident_roles import (
    ActionItemTriggerParamsIncidentConditionIncidentRoles,
)
from ..models.action_item_trigger_params_incident_condition_incident_type import (
    ActionItemTriggerParamsIncidentConditionIncidentType,
)
from ..models.action_item_trigger_params_incident_condition_kind import ActionItemTriggerParamsIncidentConditionKind
from ..models.action_item_trigger_params_incident_condition_mitigated_at_type_1 import (
    ActionItemTriggerParamsIncidentConditionMitigatedAtType1,
)
from ..models.action_item_trigger_params_incident_condition_resolved_at_type_1 import (
    ActionItemTriggerParamsIncidentConditionResolvedAtType1,
)
from ..models.action_item_trigger_params_incident_condition_service import (
    ActionItemTriggerParamsIncidentConditionService,
)
from ..models.action_item_trigger_params_incident_condition_severity import (
    ActionItemTriggerParamsIncidentConditionSeverity,
)
from ..models.action_item_trigger_params_incident_condition_started_at_type_1 import (
    ActionItemTriggerParamsIncidentConditionStartedAtType1,
)
from ..models.action_item_trigger_params_incident_condition_status import ActionItemTriggerParamsIncidentConditionStatus
from ..models.action_item_trigger_params_incident_condition_sub_status import (
    ActionItemTriggerParamsIncidentConditionSubStatus,
)
from ..models.action_item_trigger_params_incident_condition_summary_type_1 import (
    ActionItemTriggerParamsIncidentConditionSummaryType1,
)
from ..models.action_item_trigger_params_incident_condition_visibility import (
    ActionItemTriggerParamsIncidentConditionVisibility,
)
from ..models.action_item_trigger_params_incident_conditional_inactivity_type_1 import (
    ActionItemTriggerParamsIncidentConditionalInactivityType1,
)
from ..models.action_item_trigger_params_incident_kinds_item import ActionItemTriggerParamsIncidentKindsItem
from ..models.action_item_trigger_params_incident_statuses_item import ActionItemTriggerParamsIncidentStatusesItem
from ..models.action_item_trigger_params_trigger_type import ActionItemTriggerParamsTriggerType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ActionItemTriggerParams")


@_attrs_define
class ActionItemTriggerParams:
    """
    Attributes:
        trigger_type (ActionItemTriggerParamsTriggerType):
        triggers (Union[Unset, list[str]]):
        incident_visibilities (Union[Unset, list[bool]]):
        incident_kinds (Union[Unset, list[ActionItemTriggerParamsIncidentKindsItem]]):
        incident_statuses (Union[Unset, list[ActionItemTriggerParamsIncidentStatusesItem]]):
        incident_inactivity_duration (Union[None, Unset, str]):
        incident_condition (Union[Unset, ActionItemTriggerParamsIncidentCondition]):  Default:
            ActionItemTriggerParamsIncidentCondition.ALL.
        incident_condition_visibility (Union[Unset, ActionItemTriggerParamsIncidentConditionVisibility]):  Default:
            ActionItemTriggerParamsIncidentConditionVisibility.ANY.
        incident_condition_kind (Union[Unset, ActionItemTriggerParamsIncidentConditionKind]):  Default:
            ActionItemTriggerParamsIncidentConditionKind.IS.
        incident_condition_status (Union[Unset, ActionItemTriggerParamsIncidentConditionStatus]):  Default:
            ActionItemTriggerParamsIncidentConditionStatus.ANY.
        incident_condition_sub_status (Union[Unset, ActionItemTriggerParamsIncidentConditionSubStatus]):  Default:
            ActionItemTriggerParamsIncidentConditionSubStatus.ANY.
        incident_condition_environment (Union[Unset, ActionItemTriggerParamsIncidentConditionEnvironment]):  Default:
            ActionItemTriggerParamsIncidentConditionEnvironment.ANY.
        incident_condition_severity (Union[Unset, ActionItemTriggerParamsIncidentConditionSeverity]):  Default:
            ActionItemTriggerParamsIncidentConditionSeverity.ANY.
        incident_condition_incident_type (Union[Unset, ActionItemTriggerParamsIncidentConditionIncidentType]):  Default:
            ActionItemTriggerParamsIncidentConditionIncidentType.ANY.
        incident_condition_incident_roles (Union[Unset, ActionItemTriggerParamsIncidentConditionIncidentRoles]):
            Default: ActionItemTriggerParamsIncidentConditionIncidentRoles.ANY.
        incident_condition_service (Union[Unset, ActionItemTriggerParamsIncidentConditionService]):  Default:
            ActionItemTriggerParamsIncidentConditionService.ANY.
        incident_condition_functionality (Union[Unset, ActionItemTriggerParamsIncidentConditionFunctionality]):
            Default: ActionItemTriggerParamsIncidentConditionFunctionality.ANY.
        incident_condition_group (Union[Unset, ActionItemTriggerParamsIncidentConditionGroup]):  Default:
            ActionItemTriggerParamsIncidentConditionGroup.ANY.
        incident_condition_summary (Union[ActionItemTriggerParamsIncidentConditionSummaryType1, None, Unset]):
        incident_condition_started_at (Union[ActionItemTriggerParamsIncidentConditionStartedAtType1, None, Unset]):
        incident_condition_detected_at (Union[ActionItemTriggerParamsIncidentConditionDetectedAtType1, None, Unset]):
        incident_condition_acknowledged_at (Union[ActionItemTriggerParamsIncidentConditionAcknowledgedAtType1, None,
            Unset]):
        incident_condition_mitigated_at (Union[ActionItemTriggerParamsIncidentConditionMitigatedAtType1, None, Unset]):
        incident_condition_resolved_at (Union[ActionItemTriggerParamsIncidentConditionResolvedAtType1, None, Unset]):
        incident_conditional_inactivity (Union[ActionItemTriggerParamsIncidentConditionalInactivityType1, None, Unset]):
        incident_action_item_condition (Union[Unset, ActionItemTriggerParamsIncidentActionItemCondition]):
        incident_action_item_condition_kind (Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionKind]):
            Default: ActionItemTriggerParamsIncidentActionItemConditionKind.ANY.
        incident_action_item_kinds (Union[Unset, list[ActionItemTriggerParamsIncidentActionItemKindsItem]]):
        incident_action_item_condition_status (Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionStatus]):
            Default: ActionItemTriggerParamsIncidentActionItemConditionStatus.ANY.
        incident_action_item_statuses (Union[Unset, list[ActionItemTriggerParamsIncidentActionItemStatusesItem]]):
        incident_action_item_condition_priority (Union[Unset,
            ActionItemTriggerParamsIncidentActionItemConditionPriority]):  Default:
            ActionItemTriggerParamsIncidentActionItemConditionPriority.ANY.
        incident_action_item_priorities (Union[Unset, list[ActionItemTriggerParamsIncidentActionItemPrioritiesItem]]):
        incident_action_item_condition_group (Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionGroup]):
            Default: ActionItemTriggerParamsIncidentActionItemConditionGroup.ANY.
        incident_action_item_group_ids (Union[Unset, list[str]]):
    """

    trigger_type: ActionItemTriggerParamsTriggerType
    triggers: Union[Unset, list[str]] = UNSET
    incident_visibilities: Union[Unset, list[bool]] = UNSET
    incident_kinds: Union[Unset, list[ActionItemTriggerParamsIncidentKindsItem]] = UNSET
    incident_statuses: Union[Unset, list[ActionItemTriggerParamsIncidentStatusesItem]] = UNSET
    incident_inactivity_duration: Union[None, Unset, str] = UNSET
    incident_condition: Union[Unset, ActionItemTriggerParamsIncidentCondition] = (
        ActionItemTriggerParamsIncidentCondition.ALL
    )
    incident_condition_visibility: Union[Unset, ActionItemTriggerParamsIncidentConditionVisibility] = (
        ActionItemTriggerParamsIncidentConditionVisibility.ANY
    )
    incident_condition_kind: Union[Unset, ActionItemTriggerParamsIncidentConditionKind] = (
        ActionItemTriggerParamsIncidentConditionKind.IS
    )
    incident_condition_status: Union[Unset, ActionItemTriggerParamsIncidentConditionStatus] = (
        ActionItemTriggerParamsIncidentConditionStatus.ANY
    )
    incident_condition_sub_status: Union[Unset, ActionItemTriggerParamsIncidentConditionSubStatus] = (
        ActionItemTriggerParamsIncidentConditionSubStatus.ANY
    )
    incident_condition_environment: Union[Unset, ActionItemTriggerParamsIncidentConditionEnvironment] = (
        ActionItemTriggerParamsIncidentConditionEnvironment.ANY
    )
    incident_condition_severity: Union[Unset, ActionItemTriggerParamsIncidentConditionSeverity] = (
        ActionItemTriggerParamsIncidentConditionSeverity.ANY
    )
    incident_condition_incident_type: Union[Unset, ActionItemTriggerParamsIncidentConditionIncidentType] = (
        ActionItemTriggerParamsIncidentConditionIncidentType.ANY
    )
    incident_condition_incident_roles: Union[Unset, ActionItemTriggerParamsIncidentConditionIncidentRoles] = (
        ActionItemTriggerParamsIncidentConditionIncidentRoles.ANY
    )
    incident_condition_service: Union[Unset, ActionItemTriggerParamsIncidentConditionService] = (
        ActionItemTriggerParamsIncidentConditionService.ANY
    )
    incident_condition_functionality: Union[Unset, ActionItemTriggerParamsIncidentConditionFunctionality] = (
        ActionItemTriggerParamsIncidentConditionFunctionality.ANY
    )
    incident_condition_group: Union[Unset, ActionItemTriggerParamsIncidentConditionGroup] = (
        ActionItemTriggerParamsIncidentConditionGroup.ANY
    )
    incident_condition_summary: Union[ActionItemTriggerParamsIncidentConditionSummaryType1, None, Unset] = UNSET
    incident_condition_started_at: Union[ActionItemTriggerParamsIncidentConditionStartedAtType1, None, Unset] = UNSET
    incident_condition_detected_at: Union[ActionItemTriggerParamsIncidentConditionDetectedAtType1, None, Unset] = UNSET
    incident_condition_acknowledged_at: Union[
        ActionItemTriggerParamsIncidentConditionAcknowledgedAtType1, None, Unset
    ] = UNSET
    incident_condition_mitigated_at: Union[ActionItemTriggerParamsIncidentConditionMitigatedAtType1, None, Unset] = (
        UNSET
    )
    incident_condition_resolved_at: Union[ActionItemTriggerParamsIncidentConditionResolvedAtType1, None, Unset] = UNSET
    incident_conditional_inactivity: Union[ActionItemTriggerParamsIncidentConditionalInactivityType1, None, Unset] = (
        UNSET
    )
    incident_action_item_condition: Union[Unset, ActionItemTriggerParamsIncidentActionItemCondition] = UNSET
    incident_action_item_condition_kind: Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionKind] = (
        ActionItemTriggerParamsIncidentActionItemConditionKind.ANY
    )
    incident_action_item_kinds: Union[Unset, list[ActionItemTriggerParamsIncidentActionItemKindsItem]] = UNSET
    incident_action_item_condition_status: Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionStatus] = (
        ActionItemTriggerParamsIncidentActionItemConditionStatus.ANY
    )
    incident_action_item_statuses: Union[Unset, list[ActionItemTriggerParamsIncidentActionItemStatusesItem]] = UNSET
    incident_action_item_condition_priority: Union[
        Unset, ActionItemTriggerParamsIncidentActionItemConditionPriority
    ] = ActionItemTriggerParamsIncidentActionItemConditionPriority.ANY
    incident_action_item_priorities: Union[Unset, list[ActionItemTriggerParamsIncidentActionItemPrioritiesItem]] = UNSET
    incident_action_item_condition_group: Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionGroup] = (
        ActionItemTriggerParamsIncidentActionItemConditionGroup.ANY
    )
    incident_action_item_group_ids: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        trigger_type = self.trigger_type.value

        triggers: Union[Unset, list[str]] = UNSET
        if not isinstance(self.triggers, Unset):
            triggers = self.triggers

        incident_visibilities: Union[Unset, list[bool]] = UNSET
        if not isinstance(self.incident_visibilities, Unset):
            incident_visibilities = self.incident_visibilities

        incident_kinds: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_kinds, Unset):
            incident_kinds = []
            for incident_kinds_item_data in self.incident_kinds:
                incident_kinds_item = incident_kinds_item_data.value
                incident_kinds.append(incident_kinds_item)

        incident_statuses: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_statuses, Unset):
            incident_statuses = []
            for incident_statuses_item_data in self.incident_statuses:
                incident_statuses_item = incident_statuses_item_data.value
                incident_statuses.append(incident_statuses_item)

        incident_inactivity_duration: Union[None, Unset, str]
        if isinstance(self.incident_inactivity_duration, Unset):
            incident_inactivity_duration = UNSET
        else:
            incident_inactivity_duration = self.incident_inactivity_duration

        incident_condition: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition, Unset):
            incident_condition = self.incident_condition.value

        incident_condition_visibility: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_visibility, Unset):
            incident_condition_visibility = self.incident_condition_visibility.value

        incident_condition_kind: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_kind, Unset):
            incident_condition_kind = self.incident_condition_kind.value

        incident_condition_status: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_status, Unset):
            incident_condition_status = self.incident_condition_status.value

        incident_condition_sub_status: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_sub_status, Unset):
            incident_condition_sub_status = self.incident_condition_sub_status.value

        incident_condition_environment: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_environment, Unset):
            incident_condition_environment = self.incident_condition_environment.value

        incident_condition_severity: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_severity, Unset):
            incident_condition_severity = self.incident_condition_severity.value

        incident_condition_incident_type: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_incident_type, Unset):
            incident_condition_incident_type = self.incident_condition_incident_type.value

        incident_condition_incident_roles: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_incident_roles, Unset):
            incident_condition_incident_roles = self.incident_condition_incident_roles.value

        incident_condition_service: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_service, Unset):
            incident_condition_service = self.incident_condition_service.value

        incident_condition_functionality: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_functionality, Unset):
            incident_condition_functionality = self.incident_condition_functionality.value

        incident_condition_group: Union[Unset, str] = UNSET
        if not isinstance(self.incident_condition_group, Unset):
            incident_condition_group = self.incident_condition_group.value

        incident_condition_summary: Union[None, Unset, str]
        if isinstance(self.incident_condition_summary, Unset):
            incident_condition_summary = UNSET
        elif isinstance(self.incident_condition_summary, ActionItemTriggerParamsIncidentConditionSummaryType1):
            incident_condition_summary = self.incident_condition_summary.value
        else:
            incident_condition_summary = self.incident_condition_summary

        incident_condition_started_at: Union[None, Unset, str]
        if isinstance(self.incident_condition_started_at, Unset):
            incident_condition_started_at = UNSET
        elif isinstance(self.incident_condition_started_at, ActionItemTriggerParamsIncidentConditionStartedAtType1):
            incident_condition_started_at = self.incident_condition_started_at.value
        else:
            incident_condition_started_at = self.incident_condition_started_at

        incident_condition_detected_at: Union[None, Unset, str]
        if isinstance(self.incident_condition_detected_at, Unset):
            incident_condition_detected_at = UNSET
        elif isinstance(self.incident_condition_detected_at, ActionItemTriggerParamsIncidentConditionDetectedAtType1):
            incident_condition_detected_at = self.incident_condition_detected_at.value
        else:
            incident_condition_detected_at = self.incident_condition_detected_at

        incident_condition_acknowledged_at: Union[None, Unset, str]
        if isinstance(self.incident_condition_acknowledged_at, Unset):
            incident_condition_acknowledged_at = UNSET
        elif isinstance(
            self.incident_condition_acknowledged_at, ActionItemTriggerParamsIncidentConditionAcknowledgedAtType1
        ):
            incident_condition_acknowledged_at = self.incident_condition_acknowledged_at.value
        else:
            incident_condition_acknowledged_at = self.incident_condition_acknowledged_at

        incident_condition_mitigated_at: Union[None, Unset, str]
        if isinstance(self.incident_condition_mitigated_at, Unset):
            incident_condition_mitigated_at = UNSET
        elif isinstance(self.incident_condition_mitigated_at, ActionItemTriggerParamsIncidentConditionMitigatedAtType1):
            incident_condition_mitigated_at = self.incident_condition_mitigated_at.value
        else:
            incident_condition_mitigated_at = self.incident_condition_mitigated_at

        incident_condition_resolved_at: Union[None, Unset, str]
        if isinstance(self.incident_condition_resolved_at, Unset):
            incident_condition_resolved_at = UNSET
        elif isinstance(self.incident_condition_resolved_at, ActionItemTriggerParamsIncidentConditionResolvedAtType1):
            incident_condition_resolved_at = self.incident_condition_resolved_at.value
        else:
            incident_condition_resolved_at = self.incident_condition_resolved_at

        incident_conditional_inactivity: Union[None, Unset, str]
        if isinstance(self.incident_conditional_inactivity, Unset):
            incident_conditional_inactivity = UNSET
        elif isinstance(
            self.incident_conditional_inactivity, ActionItemTriggerParamsIncidentConditionalInactivityType1
        ):
            incident_conditional_inactivity = self.incident_conditional_inactivity.value
        else:
            incident_conditional_inactivity = self.incident_conditional_inactivity

        incident_action_item_condition: Union[Unset, str] = UNSET
        if not isinstance(self.incident_action_item_condition, Unset):
            incident_action_item_condition = self.incident_action_item_condition.value

        incident_action_item_condition_kind: Union[Unset, str] = UNSET
        if not isinstance(self.incident_action_item_condition_kind, Unset):
            incident_action_item_condition_kind = self.incident_action_item_condition_kind.value

        incident_action_item_kinds: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_action_item_kinds, Unset):
            incident_action_item_kinds = []
            for incident_action_item_kinds_item_data in self.incident_action_item_kinds:
                incident_action_item_kinds_item = incident_action_item_kinds_item_data.value
                incident_action_item_kinds.append(incident_action_item_kinds_item)

        incident_action_item_condition_status: Union[Unset, str] = UNSET
        if not isinstance(self.incident_action_item_condition_status, Unset):
            incident_action_item_condition_status = self.incident_action_item_condition_status.value

        incident_action_item_statuses: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_action_item_statuses, Unset):
            incident_action_item_statuses = []
            for incident_action_item_statuses_item_data in self.incident_action_item_statuses:
                incident_action_item_statuses_item = incident_action_item_statuses_item_data.value
                incident_action_item_statuses.append(incident_action_item_statuses_item)

        incident_action_item_condition_priority: Union[Unset, str] = UNSET
        if not isinstance(self.incident_action_item_condition_priority, Unset):
            incident_action_item_condition_priority = self.incident_action_item_condition_priority.value

        incident_action_item_priorities: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_action_item_priorities, Unset):
            incident_action_item_priorities = []
            for incident_action_item_priorities_item_data in self.incident_action_item_priorities:
                incident_action_item_priorities_item = incident_action_item_priorities_item_data.value
                incident_action_item_priorities.append(incident_action_item_priorities_item)

        incident_action_item_condition_group: Union[Unset, str] = UNSET
        if not isinstance(self.incident_action_item_condition_group, Unset):
            incident_action_item_condition_group = self.incident_action_item_condition_group.value

        incident_action_item_group_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.incident_action_item_group_ids, Unset):
            incident_action_item_group_ids = self.incident_action_item_group_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trigger_type": trigger_type,
            }
        )
        if triggers is not UNSET:
            field_dict["triggers"] = triggers
        if incident_visibilities is not UNSET:
            field_dict["incident_visibilities"] = incident_visibilities
        if incident_kinds is not UNSET:
            field_dict["incident_kinds"] = incident_kinds
        if incident_statuses is not UNSET:
            field_dict["incident_statuses"] = incident_statuses
        if incident_inactivity_duration is not UNSET:
            field_dict["incident_inactivity_duration"] = incident_inactivity_duration
        if incident_condition is not UNSET:
            field_dict["incident_condition"] = incident_condition
        if incident_condition_visibility is not UNSET:
            field_dict["incident_condition_visibility"] = incident_condition_visibility
        if incident_condition_kind is not UNSET:
            field_dict["incident_condition_kind"] = incident_condition_kind
        if incident_condition_status is not UNSET:
            field_dict["incident_condition_status"] = incident_condition_status
        if incident_condition_sub_status is not UNSET:
            field_dict["incident_condition_sub_status"] = incident_condition_sub_status
        if incident_condition_environment is not UNSET:
            field_dict["incident_condition_environment"] = incident_condition_environment
        if incident_condition_severity is not UNSET:
            field_dict["incident_condition_severity"] = incident_condition_severity
        if incident_condition_incident_type is not UNSET:
            field_dict["incident_condition_incident_type"] = incident_condition_incident_type
        if incident_condition_incident_roles is not UNSET:
            field_dict["incident_condition_incident_roles"] = incident_condition_incident_roles
        if incident_condition_service is not UNSET:
            field_dict["incident_condition_service"] = incident_condition_service
        if incident_condition_functionality is not UNSET:
            field_dict["incident_condition_functionality"] = incident_condition_functionality
        if incident_condition_group is not UNSET:
            field_dict["incident_condition_group"] = incident_condition_group
        if incident_condition_summary is not UNSET:
            field_dict["incident_condition_summary"] = incident_condition_summary
        if incident_condition_started_at is not UNSET:
            field_dict["incident_condition_started_at"] = incident_condition_started_at
        if incident_condition_detected_at is not UNSET:
            field_dict["incident_condition_detected_at"] = incident_condition_detected_at
        if incident_condition_acknowledged_at is not UNSET:
            field_dict["incident_condition_acknowledged_at"] = incident_condition_acknowledged_at
        if incident_condition_mitigated_at is not UNSET:
            field_dict["incident_condition_mitigated_at"] = incident_condition_mitigated_at
        if incident_condition_resolved_at is not UNSET:
            field_dict["incident_condition_resolved_at"] = incident_condition_resolved_at
        if incident_conditional_inactivity is not UNSET:
            field_dict["incident_conditional_inactivity"] = incident_conditional_inactivity
        if incident_action_item_condition is not UNSET:
            field_dict["incident_action_item_condition"] = incident_action_item_condition
        if incident_action_item_condition_kind is not UNSET:
            field_dict["incident_action_item_condition_kind"] = incident_action_item_condition_kind
        if incident_action_item_kinds is not UNSET:
            field_dict["incident_action_item_kinds"] = incident_action_item_kinds
        if incident_action_item_condition_status is not UNSET:
            field_dict["incident_action_item_condition_status"] = incident_action_item_condition_status
        if incident_action_item_statuses is not UNSET:
            field_dict["incident_action_item_statuses"] = incident_action_item_statuses
        if incident_action_item_condition_priority is not UNSET:
            field_dict["incident_action_item_condition_priority"] = incident_action_item_condition_priority
        if incident_action_item_priorities is not UNSET:
            field_dict["incident_action_item_priorities"] = incident_action_item_priorities
        if incident_action_item_condition_group is not UNSET:
            field_dict["incident_action_item_condition_group"] = incident_action_item_condition_group
        if incident_action_item_group_ids is not UNSET:
            field_dict["incident_action_item_group_ids"] = incident_action_item_group_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        trigger_type = ActionItemTriggerParamsTriggerType(d.pop("trigger_type"))

        triggers = cast(list[str], d.pop("triggers", UNSET))

        incident_visibilities = cast(list[bool], d.pop("incident_visibilities", UNSET))

        incident_kinds = []
        _incident_kinds = d.pop("incident_kinds", UNSET)
        for incident_kinds_item_data in _incident_kinds or []:
            incident_kinds_item = ActionItemTriggerParamsIncidentKindsItem(incident_kinds_item_data)

            incident_kinds.append(incident_kinds_item)

        incident_statuses = []
        _incident_statuses = d.pop("incident_statuses", UNSET)
        for incident_statuses_item_data in _incident_statuses or []:
            incident_statuses_item = ActionItemTriggerParamsIncidentStatusesItem(incident_statuses_item_data)

            incident_statuses.append(incident_statuses_item)

        def _parse_incident_inactivity_duration(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        incident_inactivity_duration = _parse_incident_inactivity_duration(d.pop("incident_inactivity_duration", UNSET))

        _incident_condition = d.pop("incident_condition", UNSET)
        incident_condition: Union[Unset, ActionItemTriggerParamsIncidentCondition]
        if isinstance(_incident_condition, Unset):
            incident_condition = UNSET
        else:
            incident_condition = ActionItemTriggerParamsIncidentCondition(_incident_condition)

        _incident_condition_visibility = d.pop("incident_condition_visibility", UNSET)
        incident_condition_visibility: Union[Unset, ActionItemTriggerParamsIncidentConditionVisibility]
        if isinstance(_incident_condition_visibility, Unset):
            incident_condition_visibility = UNSET
        else:
            incident_condition_visibility = ActionItemTriggerParamsIncidentConditionVisibility(
                _incident_condition_visibility
            )

        _incident_condition_kind = d.pop("incident_condition_kind", UNSET)
        incident_condition_kind: Union[Unset, ActionItemTriggerParamsIncidentConditionKind]
        if isinstance(_incident_condition_kind, Unset):
            incident_condition_kind = UNSET
        else:
            incident_condition_kind = ActionItemTriggerParamsIncidentConditionKind(_incident_condition_kind)

        _incident_condition_status = d.pop("incident_condition_status", UNSET)
        incident_condition_status: Union[Unset, ActionItemTriggerParamsIncidentConditionStatus]
        if isinstance(_incident_condition_status, Unset):
            incident_condition_status = UNSET
        else:
            incident_condition_status = ActionItemTriggerParamsIncidentConditionStatus(_incident_condition_status)

        _incident_condition_sub_status = d.pop("incident_condition_sub_status", UNSET)
        incident_condition_sub_status: Union[Unset, ActionItemTriggerParamsIncidentConditionSubStatus]
        if isinstance(_incident_condition_sub_status, Unset):
            incident_condition_sub_status = UNSET
        else:
            incident_condition_sub_status = ActionItemTriggerParamsIncidentConditionSubStatus(
                _incident_condition_sub_status
            )

        _incident_condition_environment = d.pop("incident_condition_environment", UNSET)
        incident_condition_environment: Union[Unset, ActionItemTriggerParamsIncidentConditionEnvironment]
        if isinstance(_incident_condition_environment, Unset):
            incident_condition_environment = UNSET
        else:
            incident_condition_environment = ActionItemTriggerParamsIncidentConditionEnvironment(
                _incident_condition_environment
            )

        _incident_condition_severity = d.pop("incident_condition_severity", UNSET)
        incident_condition_severity: Union[Unset, ActionItemTriggerParamsIncidentConditionSeverity]
        if isinstance(_incident_condition_severity, Unset):
            incident_condition_severity = UNSET
        else:
            incident_condition_severity = ActionItemTriggerParamsIncidentConditionSeverity(_incident_condition_severity)

        _incident_condition_incident_type = d.pop("incident_condition_incident_type", UNSET)
        incident_condition_incident_type: Union[Unset, ActionItemTriggerParamsIncidentConditionIncidentType]
        if isinstance(_incident_condition_incident_type, Unset):
            incident_condition_incident_type = UNSET
        else:
            incident_condition_incident_type = ActionItemTriggerParamsIncidentConditionIncidentType(
                _incident_condition_incident_type
            )

        _incident_condition_incident_roles = d.pop("incident_condition_incident_roles", UNSET)
        incident_condition_incident_roles: Union[Unset, ActionItemTriggerParamsIncidentConditionIncidentRoles]
        if isinstance(_incident_condition_incident_roles, Unset):
            incident_condition_incident_roles = UNSET
        else:
            incident_condition_incident_roles = ActionItemTriggerParamsIncidentConditionIncidentRoles(
                _incident_condition_incident_roles
            )

        _incident_condition_service = d.pop("incident_condition_service", UNSET)
        incident_condition_service: Union[Unset, ActionItemTriggerParamsIncidentConditionService]
        if isinstance(_incident_condition_service, Unset):
            incident_condition_service = UNSET
        else:
            incident_condition_service = ActionItemTriggerParamsIncidentConditionService(_incident_condition_service)

        _incident_condition_functionality = d.pop("incident_condition_functionality", UNSET)
        incident_condition_functionality: Union[Unset, ActionItemTriggerParamsIncidentConditionFunctionality]
        if isinstance(_incident_condition_functionality, Unset):
            incident_condition_functionality = UNSET
        else:
            incident_condition_functionality = ActionItemTriggerParamsIncidentConditionFunctionality(
                _incident_condition_functionality
            )

        _incident_condition_group = d.pop("incident_condition_group", UNSET)
        incident_condition_group: Union[Unset, ActionItemTriggerParamsIncidentConditionGroup]
        if isinstance(_incident_condition_group, Unset):
            incident_condition_group = UNSET
        else:
            incident_condition_group = ActionItemTriggerParamsIncidentConditionGroup(_incident_condition_group)

        def _parse_incident_condition_summary(
            data: object,
        ) -> Union[ActionItemTriggerParamsIncidentConditionSummaryType1, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                incident_condition_summary_type_1 = ActionItemTriggerParamsIncidentConditionSummaryType1(data)

                return incident_condition_summary_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ActionItemTriggerParamsIncidentConditionSummaryType1, None, Unset], data)

        incident_condition_summary = _parse_incident_condition_summary(d.pop("incident_condition_summary", UNSET))

        def _parse_incident_condition_started_at(
            data: object,
        ) -> Union[ActionItemTriggerParamsIncidentConditionStartedAtType1, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                incident_condition_started_at_type_1 = ActionItemTriggerParamsIncidentConditionStartedAtType1(data)

                return incident_condition_started_at_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ActionItemTriggerParamsIncidentConditionStartedAtType1, None, Unset], data)

        incident_condition_started_at = _parse_incident_condition_started_at(
            d.pop("incident_condition_started_at", UNSET)
        )

        def _parse_incident_condition_detected_at(
            data: object,
        ) -> Union[ActionItemTriggerParamsIncidentConditionDetectedAtType1, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                incident_condition_detected_at_type_1 = ActionItemTriggerParamsIncidentConditionDetectedAtType1(data)

                return incident_condition_detected_at_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ActionItemTriggerParamsIncidentConditionDetectedAtType1, None, Unset], data)

        incident_condition_detected_at = _parse_incident_condition_detected_at(
            d.pop("incident_condition_detected_at", UNSET)
        )

        def _parse_incident_condition_acknowledged_at(
            data: object,
        ) -> Union[ActionItemTriggerParamsIncidentConditionAcknowledgedAtType1, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                incident_condition_acknowledged_at_type_1 = ActionItemTriggerParamsIncidentConditionAcknowledgedAtType1(
                    data
                )

                return incident_condition_acknowledged_at_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ActionItemTriggerParamsIncidentConditionAcknowledgedAtType1, None, Unset], data)

        incident_condition_acknowledged_at = _parse_incident_condition_acknowledged_at(
            d.pop("incident_condition_acknowledged_at", UNSET)
        )

        def _parse_incident_condition_mitigated_at(
            data: object,
        ) -> Union[ActionItemTriggerParamsIncidentConditionMitigatedAtType1, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                incident_condition_mitigated_at_type_1 = ActionItemTriggerParamsIncidentConditionMitigatedAtType1(data)

                return incident_condition_mitigated_at_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ActionItemTriggerParamsIncidentConditionMitigatedAtType1, None, Unset], data)

        incident_condition_mitigated_at = _parse_incident_condition_mitigated_at(
            d.pop("incident_condition_mitigated_at", UNSET)
        )

        def _parse_incident_condition_resolved_at(
            data: object,
        ) -> Union[ActionItemTriggerParamsIncidentConditionResolvedAtType1, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                incident_condition_resolved_at_type_1 = ActionItemTriggerParamsIncidentConditionResolvedAtType1(data)

                return incident_condition_resolved_at_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ActionItemTriggerParamsIncidentConditionResolvedAtType1, None, Unset], data)

        incident_condition_resolved_at = _parse_incident_condition_resolved_at(
            d.pop("incident_condition_resolved_at", UNSET)
        )

        def _parse_incident_conditional_inactivity(
            data: object,
        ) -> Union[ActionItemTriggerParamsIncidentConditionalInactivityType1, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                incident_conditional_inactivity_type_1 = ActionItemTriggerParamsIncidentConditionalInactivityType1(data)

                return incident_conditional_inactivity_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ActionItemTriggerParamsIncidentConditionalInactivityType1, None, Unset], data)

        incident_conditional_inactivity = _parse_incident_conditional_inactivity(
            d.pop("incident_conditional_inactivity", UNSET)
        )

        _incident_action_item_condition = d.pop("incident_action_item_condition", UNSET)
        incident_action_item_condition: Union[Unset, ActionItemTriggerParamsIncidentActionItemCondition]
        if isinstance(_incident_action_item_condition, Unset):
            incident_action_item_condition = UNSET
        else:
            incident_action_item_condition = ActionItemTriggerParamsIncidentActionItemCondition(
                _incident_action_item_condition
            )

        _incident_action_item_condition_kind = d.pop("incident_action_item_condition_kind", UNSET)
        incident_action_item_condition_kind: Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionKind]
        if isinstance(_incident_action_item_condition_kind, Unset):
            incident_action_item_condition_kind = UNSET
        else:
            incident_action_item_condition_kind = ActionItemTriggerParamsIncidentActionItemConditionKind(
                _incident_action_item_condition_kind
            )

        incident_action_item_kinds = []
        _incident_action_item_kinds = d.pop("incident_action_item_kinds", UNSET)
        for incident_action_item_kinds_item_data in _incident_action_item_kinds or []:
            incident_action_item_kinds_item = ActionItemTriggerParamsIncidentActionItemKindsItem(
                incident_action_item_kinds_item_data
            )

            incident_action_item_kinds.append(incident_action_item_kinds_item)

        _incident_action_item_condition_status = d.pop("incident_action_item_condition_status", UNSET)
        incident_action_item_condition_status: Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionStatus]
        if isinstance(_incident_action_item_condition_status, Unset):
            incident_action_item_condition_status = UNSET
        else:
            incident_action_item_condition_status = ActionItemTriggerParamsIncidentActionItemConditionStatus(
                _incident_action_item_condition_status
            )

        incident_action_item_statuses = []
        _incident_action_item_statuses = d.pop("incident_action_item_statuses", UNSET)
        for incident_action_item_statuses_item_data in _incident_action_item_statuses or []:
            incident_action_item_statuses_item = ActionItemTriggerParamsIncidentActionItemStatusesItem(
                incident_action_item_statuses_item_data
            )

            incident_action_item_statuses.append(incident_action_item_statuses_item)

        _incident_action_item_condition_priority = d.pop("incident_action_item_condition_priority", UNSET)
        incident_action_item_condition_priority: Union[
            Unset, ActionItemTriggerParamsIncidentActionItemConditionPriority
        ]
        if isinstance(_incident_action_item_condition_priority, Unset):
            incident_action_item_condition_priority = UNSET
        else:
            incident_action_item_condition_priority = ActionItemTriggerParamsIncidentActionItemConditionPriority(
                _incident_action_item_condition_priority
            )

        incident_action_item_priorities = []
        _incident_action_item_priorities = d.pop("incident_action_item_priorities", UNSET)
        for incident_action_item_priorities_item_data in _incident_action_item_priorities or []:
            incident_action_item_priorities_item = ActionItemTriggerParamsIncidentActionItemPrioritiesItem(
                incident_action_item_priorities_item_data
            )

            incident_action_item_priorities.append(incident_action_item_priorities_item)

        _incident_action_item_condition_group = d.pop("incident_action_item_condition_group", UNSET)
        incident_action_item_condition_group: Union[Unset, ActionItemTriggerParamsIncidentActionItemConditionGroup]
        if isinstance(_incident_action_item_condition_group, Unset):
            incident_action_item_condition_group = UNSET
        else:
            incident_action_item_condition_group = ActionItemTriggerParamsIncidentActionItemConditionGroup(
                _incident_action_item_condition_group
            )

        incident_action_item_group_ids = cast(list[str], d.pop("incident_action_item_group_ids", UNSET))

        action_item_trigger_params = cls(
            trigger_type=trigger_type,
            triggers=triggers,
            incident_visibilities=incident_visibilities,
            incident_kinds=incident_kinds,
            incident_statuses=incident_statuses,
            incident_inactivity_duration=incident_inactivity_duration,
            incident_condition=incident_condition,
            incident_condition_visibility=incident_condition_visibility,
            incident_condition_kind=incident_condition_kind,
            incident_condition_status=incident_condition_status,
            incident_condition_sub_status=incident_condition_sub_status,
            incident_condition_environment=incident_condition_environment,
            incident_condition_severity=incident_condition_severity,
            incident_condition_incident_type=incident_condition_incident_type,
            incident_condition_incident_roles=incident_condition_incident_roles,
            incident_condition_service=incident_condition_service,
            incident_condition_functionality=incident_condition_functionality,
            incident_condition_group=incident_condition_group,
            incident_condition_summary=incident_condition_summary,
            incident_condition_started_at=incident_condition_started_at,
            incident_condition_detected_at=incident_condition_detected_at,
            incident_condition_acknowledged_at=incident_condition_acknowledged_at,
            incident_condition_mitigated_at=incident_condition_mitigated_at,
            incident_condition_resolved_at=incident_condition_resolved_at,
            incident_conditional_inactivity=incident_conditional_inactivity,
            incident_action_item_condition=incident_action_item_condition,
            incident_action_item_condition_kind=incident_action_item_condition_kind,
            incident_action_item_kinds=incident_action_item_kinds,
            incident_action_item_condition_status=incident_action_item_condition_status,
            incident_action_item_statuses=incident_action_item_statuses,
            incident_action_item_condition_priority=incident_action_item_condition_priority,
            incident_action_item_priorities=incident_action_item_priorities,
            incident_action_item_condition_group=incident_action_item_condition_group,
            incident_action_item_group_ids=incident_action_item_group_ids,
        )

        action_item_trigger_params.additional_properties = d
        return action_item_trigger_params

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
