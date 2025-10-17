from enum import Enum


class GeniusCreateGoogleGeminiChatCompletionTaskParamsTaskType(str, Enum):
    GENIUS_CREATE_GOOGLE_GEMINI_CHAT_COMPLETION_TASK = "genius_create_google_gemini_chat_completion_task"

    def __str__(self) -> str:
        return str(self.value)
