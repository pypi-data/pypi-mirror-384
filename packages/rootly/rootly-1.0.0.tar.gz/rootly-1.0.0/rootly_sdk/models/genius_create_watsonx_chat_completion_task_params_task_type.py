from enum import Enum


class GeniusCreateWatsonxChatCompletionTaskParamsTaskType(str, Enum):
    GENIUS_CREATE_WATSONX_CHAT_COMPLETION_TASK = "genius_create_watsonx_chat_completion_task"

    def __str__(self) -> str:
        return str(self.value)
