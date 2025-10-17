from enum import Enum


class InviteToSlackChannelVictorOpsTaskParamsTaskType(str, Enum):
    INVITE_TO_SLACK_CHANNEL_VICTOR_OPS = "invite_to_slack_channel_victor_ops"

    def __str__(self) -> str:
        return str(self.value)
