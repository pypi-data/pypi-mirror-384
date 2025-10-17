from enum import Enum


class UpdatePagertreeAlertTaskParamsTaskType(str, Enum):
    UPDATE_PAGERTREE_ALERT = "update_pagertree_alert"

    def __str__(self) -> str:
        return str(self.value)
