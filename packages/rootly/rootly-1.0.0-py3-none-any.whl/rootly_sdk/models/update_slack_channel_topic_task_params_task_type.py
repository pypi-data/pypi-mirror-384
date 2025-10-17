from enum import Enum


class UpdateSlackChannelTopicTaskParamsTaskType(str, Enum):
    UPDATE_SLACK_CHANNEL_TOPIC = "update_slack_channel_topic"

    def __str__(self) -> str:
        return str(self.value)
