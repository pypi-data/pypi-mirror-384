from enum import Enum


class TweetTwitterMessageTaskParamsTaskType(str, Enum):
    TWEET_TWITTER_MESSAGE = "tweet_twitter_message"

    def __str__(self) -> str:
        return str(self.value)
