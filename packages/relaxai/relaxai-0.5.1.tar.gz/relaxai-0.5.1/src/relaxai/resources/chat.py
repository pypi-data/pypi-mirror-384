# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable

import httpx

from ..types import chat_create_completion_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.stream_options_param import StreamOptionsParam
from ..types.chat_completion_response import ChatCompletionResponse
from ..types.function_definition_param import FunctionDefinitionParam
from ..types.chat_completion_message_param import ChatCompletionMessageParam

__all__ = ["ChatResource", "AsyncChatResource"]


class ChatResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/relax-ai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/relax-ai/python-sdk#with_streaming_response
        """
        return ChatResourceWithStreamingResponse(self)

    def create_completion(
        self,
        *,
        messages: Iterable[ChatCompletionMessageParam],
        model: str,
        query_stream: bool | Omit = omit,
        chat_template_kwargs: chat_create_completion_params.ChatTemplateKwargs | Omit = omit,
        frequency_penalty: float | Omit = omit,
        function_call: chat_create_completion_params.FunctionCall | Omit = omit,
        functions: Iterable[FunctionDefinitionParam] | Omit = omit,
        logit_bias: Dict[str, int] | Omit = omit,
        logprobs: bool | Omit = omit,
        max_completion_tokens: int | Omit = omit,
        max_tokens: int | Omit = omit,
        metadata: Dict[str, str] | Omit = omit,
        n: int | Omit = omit,
        parallel_tool_calls: chat_create_completion_params.ParallelToolCalls | Omit = omit,
        prediction: chat_create_completion_params.Prediction | Omit = omit,
        presence_penalty: float | Omit = omit,
        reasoning_effort: str | Omit = omit,
        response_format: chat_create_completion_params.ResponseFormat | Omit = omit,
        seed: int | Omit = omit,
        stop: SequenceNotStr[str] | Omit = omit,
        store: bool | Omit = omit,
        body_stream: bool | Omit = omit,
        stream_options: StreamOptionsParam | Omit = omit,
        temperature: float | Omit = omit,
        tool_choice: chat_create_completion_params.ToolChoice | Omit = omit,
        tools: Iterable[chat_create_completion_params.Tool] | Omit = omit,
        top_logprobs: int | Omit = omit,
        top_p: float | Omit = omit,
        user: str | Omit = omit,
        web_search_options: chat_create_completion_params.WebSearchOptions | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatCompletionResponse:
        """
        Creates a chat completion for the given model

        Args:
          query_stream: If true, server responds as an SSE stream. Generators may produce an ergonomic
              streaming method when this is set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/chat/completions",
            body=maybe_transform(
                {
                    "messages": messages,
                    "model": model,
                    "chat_template_kwargs": chat_template_kwargs,
                    "frequency_penalty": frequency_penalty,
                    "function_call": function_call,
                    "functions": functions,
                    "logit_bias": logit_bias,
                    "logprobs": logprobs,
                    "max_completion_tokens": max_completion_tokens,
                    "max_tokens": max_tokens,
                    "metadata": metadata,
                    "n": n,
                    "parallel_tool_calls": parallel_tool_calls,
                    "prediction": prediction,
                    "presence_penalty": presence_penalty,
                    "reasoning_effort": reasoning_effort,
                    "response_format": response_format,
                    "seed": seed,
                    "stop": stop,
                    "store": store,
                    "body_stream": body_stream,
                    "stream_options": stream_options,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_logprobs": top_logprobs,
                    "top_p": top_p,
                    "user": user,
                    "web_search_options": web_search_options,
                },
                chat_create_completion_params.ChatCreateCompletionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"query_stream": query_stream}, chat_create_completion_params.ChatCreateCompletionParams
                ),
            ),
            cast_to=ChatCompletionResponse,
        )


class AsyncChatResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncChatResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/relax-ai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncChatResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChatResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/relax-ai/python-sdk#with_streaming_response
        """
        return AsyncChatResourceWithStreamingResponse(self)

    async def create_completion(
        self,
        *,
        messages: Iterable[ChatCompletionMessageParam],
        model: str,
        query_stream: bool | Omit = omit,
        chat_template_kwargs: chat_create_completion_params.ChatTemplateKwargs | Omit = omit,
        frequency_penalty: float | Omit = omit,
        function_call: chat_create_completion_params.FunctionCall | Omit = omit,
        functions: Iterable[FunctionDefinitionParam] | Omit = omit,
        logit_bias: Dict[str, int] | Omit = omit,
        logprobs: bool | Omit = omit,
        max_completion_tokens: int | Omit = omit,
        max_tokens: int | Omit = omit,
        metadata: Dict[str, str] | Omit = omit,
        n: int | Omit = omit,
        parallel_tool_calls: chat_create_completion_params.ParallelToolCalls | Omit = omit,
        prediction: chat_create_completion_params.Prediction | Omit = omit,
        presence_penalty: float | Omit = omit,
        reasoning_effort: str | Omit = omit,
        response_format: chat_create_completion_params.ResponseFormat | Omit = omit,
        seed: int | Omit = omit,
        stop: SequenceNotStr[str] | Omit = omit,
        store: bool | Omit = omit,
        body_stream: bool | Omit = omit,
        stream_options: StreamOptionsParam | Omit = omit,
        temperature: float | Omit = omit,
        tool_choice: chat_create_completion_params.ToolChoice | Omit = omit,
        tools: Iterable[chat_create_completion_params.Tool] | Omit = omit,
        top_logprobs: int | Omit = omit,
        top_p: float | Omit = omit,
        user: str | Omit = omit,
        web_search_options: chat_create_completion_params.WebSearchOptions | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatCompletionResponse:
        """
        Creates a chat completion for the given model

        Args:
          query_stream: If true, server responds as an SSE stream. Generators may produce an ergonomic
              streaming method when this is set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/chat/completions",
            body=await async_maybe_transform(
                {
                    "messages": messages,
                    "model": model,
                    "chat_template_kwargs": chat_template_kwargs,
                    "frequency_penalty": frequency_penalty,
                    "function_call": function_call,
                    "functions": functions,
                    "logit_bias": logit_bias,
                    "logprobs": logprobs,
                    "max_completion_tokens": max_completion_tokens,
                    "max_tokens": max_tokens,
                    "metadata": metadata,
                    "n": n,
                    "parallel_tool_calls": parallel_tool_calls,
                    "prediction": prediction,
                    "presence_penalty": presence_penalty,
                    "reasoning_effort": reasoning_effort,
                    "response_format": response_format,
                    "seed": seed,
                    "stop": stop,
                    "store": store,
                    "body_stream": body_stream,
                    "stream_options": stream_options,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_logprobs": top_logprobs,
                    "top_p": top_p,
                    "user": user,
                    "web_search_options": web_search_options,
                },
                chat_create_completion_params.ChatCreateCompletionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"query_stream": query_stream}, chat_create_completion_params.ChatCreateCompletionParams
                ),
            ),
            cast_to=ChatCompletionResponse,
        )


class ChatResourceWithRawResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.create_completion = to_raw_response_wrapper(
            chat.create_completion,
        )


class AsyncChatResourceWithRawResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.create_completion = async_to_raw_response_wrapper(
            chat.create_completion,
        )


class ChatResourceWithStreamingResponse:
    def __init__(self, chat: ChatResource) -> None:
        self._chat = chat

        self.create_completion = to_streamed_response_wrapper(
            chat.create_completion,
        )


class AsyncChatResourceWithStreamingResponse:
    def __init__(self, chat: AsyncChatResource) -> None:
        self._chat = chat

        self.create_completion = async_to_streamed_response_wrapper(
            chat.create_completion,
        )
