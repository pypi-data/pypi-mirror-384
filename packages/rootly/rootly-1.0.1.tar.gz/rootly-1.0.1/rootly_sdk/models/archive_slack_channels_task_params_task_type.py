from typing import Literal, cast

ArchiveSlackChannelsTaskParamsTaskType = Literal["archive_slack_channels"]

ARCHIVE_SLACK_CHANNELS_TASK_PARAMS_TASK_TYPE_VALUES: set[ArchiveSlackChannelsTaskParamsTaskType] = {
    "archive_slack_channels",
}


def check_archive_slack_channels_task_params_task_type(value: str) -> ArchiveSlackChannelsTaskParamsTaskType:
    if value in ARCHIVE_SLACK_CHANNELS_TASK_PARAMS_TASK_TYPE_VALUES:
        return cast(ArchiveSlackChannelsTaskParamsTaskType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {ARCHIVE_SLACK_CHANNELS_TASK_PARAMS_TASK_TYPE_VALUES!r}"
    )
