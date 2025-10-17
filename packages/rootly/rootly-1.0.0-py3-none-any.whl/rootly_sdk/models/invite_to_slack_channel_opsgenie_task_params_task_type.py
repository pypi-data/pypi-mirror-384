from enum import Enum


class InviteToSlackChannelOpsgenieTaskParamsTaskType(str, Enum):
    INVITE_TO_SLACK_CHANNEL_OPSGENIE = "invite_to_slack_channel_opsgenie"

    def __str__(self) -> str:
        return str(self.value)
