from enum import Enum


class UpdateDashboardPanelDataAttributesParamsDatasetsItemFilterItemRulesItemCondition(str, Enum):
    CONTAINS = "contains"
    EXISTS = "exists"
    NOT_CONTAINS = "not_contains"
    NOT_EXISTS = "not_exists"
    VALUE_0 = "="
    VALUE_1 = "!="
    VALUE_2 = ">="
    VALUE_3 = "<="

    def __str__(self) -> str:
        return str(self.value)
