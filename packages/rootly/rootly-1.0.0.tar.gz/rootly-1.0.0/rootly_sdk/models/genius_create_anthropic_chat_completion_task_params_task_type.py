from enum import Enum


class GeniusCreateAnthropicChatCompletionTaskParamsTaskType(str, Enum):
    GENIUS_CREATE_ANTHROPIC_CHAT_COMPLETION_TASK = "genius_create_anthropic_chat_completion_task"

    def __str__(self) -> str:
        return str(self.value)
