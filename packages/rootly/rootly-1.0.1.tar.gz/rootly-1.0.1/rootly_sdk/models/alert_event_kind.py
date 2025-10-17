from typing import Literal, cast

AlertEventKind = Literal[
    "action",
    "alert_grouping",
    "alert_routing",
    "alert_urgency",
    "informational",
    "maintenance",
    "noise",
    "note",
    "notification",
    "recording",
    "status_update",
]

ALERT_EVENT_KIND_VALUES: set[AlertEventKind] = {
    "action",
    "alert_grouping",
    "alert_routing",
    "alert_urgency",
    "informational",
    "maintenance",
    "noise",
    "note",
    "notification",
    "recording",
    "status_update",
}


def check_alert_event_kind(value: str) -> AlertEventKind:
    if value in ALERT_EVENT_KIND_VALUES:
        return cast(AlertEventKind, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {ALERT_EVENT_KIND_VALUES!r}")
