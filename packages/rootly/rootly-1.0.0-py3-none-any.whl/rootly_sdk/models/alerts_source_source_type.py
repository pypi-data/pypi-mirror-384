from enum import Enum


class AlertsSourceSourceType(str, Enum):
    ALERTMANAGER = "alertmanager"
    APP_DYNAMICS = "app_dynamics"
    APP_OPTICS = "app_optics"
    AZURE = "azure"
    BUG_SNAG = "bug_snag"
    CATCHPOINT = "catchpoint"
    CHECKLY = "checkly"
    CHRONOSPHERE = "chronosphere"
    CLOUD_WATCH = "cloud_watch"
    DATADOG = "datadog"
    EMAIL = "email"
    GENERIC_WEBHOOK = "generic_webhook"
    GOOGLE_CLOUD = "google_cloud"
    GRAFANA = "grafana"
    HONEYCOMB = "honeycomb"
    MONTE_CARLO = "monte_carlo"
    NAGIOS = "nagios"
    NEW_RELIC = "new_relic"
    PRTG = "prtg"
    SENTRY = "sentry"
    SPLUNK = "splunk"

    def __str__(self) -> str:
        return str(self.value)
