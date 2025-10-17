from enum import Enum


class CreateSlackChannelTaskParamsTaskType(str, Enum):
    CREATE_SLACK_CHANNEL = "create_slack_channel"

    def __str__(self) -> str:
        return str(self.value)
