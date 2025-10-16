from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict


class ContainerBody(TypedDict, total=False):
    container_id: str
    model: str
    system_prompt: str
    endpoint: str
    # allow extras


class Container(TypedDict, total=False):
    id: str
    label: str
    inference_body: ContainerBody


class ContainerCreateParams(TypedDict, total=False):
    label: str
    initial_model: str
    initial_system_prompt: str
    base_models: List[str]
    optimization_config: Dict[str, Any]


class ContainerGetParams(TypedDict, total=False):
    label: str


class ModelsList(TypedDict):
    data: List[Dict[str, Any]]


Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(TypedDict, total=False):
    role: Role
    content: str


class ChatCompletionCreateParams(TypedDict, total=False):
    model: Optional[str]
    container: Optional[Container]
    messages: List[ChatMessage]
    max_tokens: Optional[int]
    temperature: Optional[float]


class ChoiceMessage(TypedDict, total=False):
    role: Literal["assistant"]
    content: str


class ChatCompletionChoice(TypedDict, total=False):
    index: int
    message: ChoiceMessage
    finish_reason: Optional[str]


class Usage(TypedDict, total=False):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: Optional[int]
    input_cache_read: Optional[int]
    input_cache_write: Optional[int]
    output_cache_read: Optional[int]
    output_cache_write: Optional[int]
    internal_reasoning: Optional[int]
    web_search: Optional[int]
    request_tokens: Optional[int]


class ChatCompletion(TypedDict, total=False):
    id: str
    object: Literal["chat.completion"]
    model: str
    created: Optional[int]
    choices: List[ChatCompletionChoice]
    usage: Usage


class Delta(TypedDict, total=False):
    role: Optional[Literal["assistant", "system", "user"]]
    content: Optional[str]


class ChatCompletionChunkChoice(TypedDict, total=False):
    index: int
    delta: Delta
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]]


class ChatCompletionChunk(TypedDict, total=False):
    id: str
    object: Literal["chat.completion.chunk"]
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]


class ManiacOptions(TypedDict, total=False):
    apiKey: Optional[str]
    baseURL: Optional[str]
    verifySSL: Optional[bool]
    caBundlePath: Optional[str]


class RegisterCompletionsSuccess(TypedDict, total=False):
    status: Literal["ok"]
    label: str
    dataCount: int
    raw: Any


class ManiacRequestError(Exception):
    def __init__(
        self,
        errorType: Literal[
            "validation_error",
            "http_error",
            "request_error",
            "unknown_error",
        ],
        message: str,
        statusCode: Optional[int] = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.name = "ManiacRequestError"
        self.errorType = errorType
        self.statusCode = statusCode
        self.details = details

    def toJSON(self) -> Dict[str, Any]:
        return {
            "status": "error",
            "errorType": self.errorType,
            "statusCode": self.statusCode,
            "message": str(self),
            "details": self.details,
        }


class RawCompletionDatapoint(TypedDict, total=False):
    messages: List[ChatMessage]
    # extras allowed


class ConvertedDatapoint(TypedDict, total=False):
    input: List[ChatMessage]
    output: str
    system_prompt: Optional[str]
    additional_parameters: Optional[Dict[str, Any]]


class RegisterCompletionsParams(TypedDict, total=False):
    container: Container
    dataset: List[RawCompletionDatapoint]
