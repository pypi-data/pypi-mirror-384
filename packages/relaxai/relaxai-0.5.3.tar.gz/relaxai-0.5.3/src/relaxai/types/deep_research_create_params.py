# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr
from .stream_options_param import StreamOptionsParam
from .function_definition_param import FunctionDefinitionParam
from .chat_completion_message_param import ChatCompletionMessageParam

__all__ = ["DeepResearchCreateParams", "ResponseFormat", "ResponseFormatJsonSchema", "Tool"]


class DeepResearchCreateParams(TypedDict, total=False):
    messages: Required[Iterable[ChatCompletionMessageParam]]

    model: Required[str]

    max_tokens: int

    response_format: ResponseFormat

    stop: SequenceNotStr[str]

    stream: bool

    stream_options: StreamOptionsParam

    temperature: float

    tool_choice: object

    tools: Iterable[Tool]

    top_p: float


class ResponseFormatJsonSchema(TypedDict, total=False):
    description: str

    name: str

    schema: str

    strict: bool


class ResponseFormat(TypedDict, total=False):
    json_schema: ResponseFormatJsonSchema

    type: str


class Tool(TypedDict, total=False):
    type: Required[str]

    function: FunctionDefinitionParam
