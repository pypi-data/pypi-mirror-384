# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .function_call import FunctionCall
from .shared.openai_usage import OpenAIUsage

__all__ = [
    "DeepresearchResponse",
    "Choice",
    "ChoiceMessage",
    "ChoiceMessageAnnotation",
    "ChoiceMessageAnnotationURLCitation",
    "ChoiceMessageToolCall",
    "ChoiceLogprobs",
    "ChoiceLogprobsContent",
    "ChoiceLogprobsContentTopLogprob",
]


class ChoiceMessageAnnotationURLCitation(BaseModel):
    end_index: int

    start_index: int

    title: str

    url: str


class ChoiceMessageAnnotation(BaseModel):
    type: str

    url_citation: Optional[ChoiceMessageAnnotationURLCitation] = None


class ChoiceMessageToolCall(BaseModel):
    function: FunctionCall

    type: str

    id: Optional[str] = None

    index: Optional[int] = None


class ChoiceMessage(BaseModel):
    role: str

    annotations: Optional[List[ChoiceMessageAnnotation]] = None

    content: Optional[str] = None

    function_call: Optional[FunctionCall] = None

    name: Optional[str] = None

    reasoning_content: Optional[str] = None

    refusal: Optional[str] = None

    tool_call_id: Optional[str] = None

    tool_calls: Optional[List[ChoiceMessageToolCall]] = None


class ChoiceLogprobsContentTopLogprob(BaseModel):
    token: str

    logprob: float

    bytes: Optional[str] = None


class ChoiceLogprobsContent(BaseModel):
    token: str

    logprob: float

    top_logprobs: List[ChoiceLogprobsContentTopLogprob]

    bytes: Optional[str] = None


class ChoiceLogprobs(BaseModel):
    content: List[ChoiceLogprobsContent]


class Choice(BaseModel):
    finish_reason: str

    index: int

    message: ChoiceMessage

    logprobs: Optional[ChoiceLogprobs] = None


class DeepresearchResponse(BaseModel):
    id: str

    choices: List[Choice]

    created: int

    model: str

    object: str

    system_fingerprint: str

    usage: OpenAIUsage

    service_tier: Optional[str] = None
