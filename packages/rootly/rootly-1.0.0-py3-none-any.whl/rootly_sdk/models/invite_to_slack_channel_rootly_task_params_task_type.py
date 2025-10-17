from enum import Enum


class InviteToSlackChannelRootlyTaskParamsTaskType(str, Enum):
    INVITE_TO_SLACK_CHANNEL_ROOTLY = "invite_to_slack_channel_rootly"

    def __str__(self) -> str:
        return str(self.value)
