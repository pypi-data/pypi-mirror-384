from enum import Enum


class ListPlaybooksInclude(str, Enum):
    CAUSES = "causes"
    ENVIRONMENTS = "environments"
    FUNCTIONALITIES = "functionalities"
    GROUPS = "groups"
    INCIDENT_TYPES = "incident_types"
    SERVICES = "services"
    SEVERITIES = "severities"

    def __str__(self) -> str:
        return str(self.value)
