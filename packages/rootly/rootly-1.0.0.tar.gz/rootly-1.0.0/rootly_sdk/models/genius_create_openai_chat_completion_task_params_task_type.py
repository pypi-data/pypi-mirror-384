from enum import Enum


class GeniusCreateOpenaiChatCompletionTaskParamsTaskType(str, Enum):
    GENIUS_OPENAI_CHAT_COMPLETION = "genius_openai_chat_completion"

    def __str__(self) -> str:
        return str(self.value)
