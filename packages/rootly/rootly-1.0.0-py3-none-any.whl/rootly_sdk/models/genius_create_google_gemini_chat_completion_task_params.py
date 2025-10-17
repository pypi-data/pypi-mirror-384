from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.genius_create_google_gemini_chat_completion_task_params_task_type import (
    GeniusCreateGoogleGeminiChatCompletionTaskParamsTaskType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.genius_create_google_gemini_chat_completion_task_params_model import (
        GeniusCreateGoogleGeminiChatCompletionTaskParamsModel,
    )


T = TypeVar("T", bound="GeniusCreateGoogleGeminiChatCompletionTaskParams")


@_attrs_define
class GeniusCreateGoogleGeminiChatCompletionTaskParams:
    """
    Attributes:
        model (GeniusCreateGoogleGeminiChatCompletionTaskParamsModel): The Gemini model. eg: gemini-2.0-flash
        prompt (str): The prompt to send to Gemini
        task_type (Union[Unset, GeniusCreateGoogleGeminiChatCompletionTaskParamsTaskType]):
        system_prompt (Union[Unset, str]): The system prompt to send to Gemini (optional)
    """

    model: "GeniusCreateGoogleGeminiChatCompletionTaskParamsModel"
    prompt: str
    task_type: Union[Unset, GeniusCreateGoogleGeminiChatCompletionTaskParamsTaskType] = UNSET
    system_prompt: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model = self.model.to_dict()

        prompt = self.prompt

        task_type: Union[Unset, str] = UNSET
        if not isinstance(self.task_type, Unset):
            task_type = self.task_type.value

        system_prompt = self.system_prompt

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model": model,
                "prompt": prompt,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type
        if system_prompt is not UNSET:
            field_dict["system_prompt"] = system_prompt

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.genius_create_google_gemini_chat_completion_task_params_model import (
            GeniusCreateGoogleGeminiChatCompletionTaskParamsModel,
        )

        d = src_dict.copy()
        model = GeniusCreateGoogleGeminiChatCompletionTaskParamsModel.from_dict(d.pop("model"))

        prompt = d.pop("prompt")

        _task_type = d.pop("task_type", UNSET)
        task_type: Union[Unset, GeniusCreateGoogleGeminiChatCompletionTaskParamsTaskType]
        if isinstance(_task_type, Unset):
            task_type = UNSET
        else:
            task_type = GeniusCreateGoogleGeminiChatCompletionTaskParamsTaskType(_task_type)

        system_prompt = d.pop("system_prompt", UNSET)

        genius_create_google_gemini_chat_completion_task_params = cls(
            model=model,
            prompt=prompt,
            task_type=task_type,
            system_prompt=system_prompt,
        )

        genius_create_google_gemini_chat_completion_task_params.additional_properties = d
        return genius_create_google_gemini_chat_completion_task_params

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
