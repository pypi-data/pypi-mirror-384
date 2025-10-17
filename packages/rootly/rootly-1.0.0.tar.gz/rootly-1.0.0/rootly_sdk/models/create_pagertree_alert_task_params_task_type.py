from enum import Enum


class CreatePagertreeAlertTaskParamsTaskType(str, Enum):
    CREATE_PAGERTREE_ALERT = "create_pagertree_alert"

    def __str__(self) -> str:
        return str(self.value)
