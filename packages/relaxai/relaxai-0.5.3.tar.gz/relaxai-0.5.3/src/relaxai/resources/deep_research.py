# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ..types import deep_research_create_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import is_given, maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._constants import DEFAULT_TIMEOUT
from .._base_client import make_request_options
from ..types.stream_options_param import StreamOptionsParam
from ..types.deepresearch_response import DeepresearchResponse
from ..types.chat_completion_message_param import ChatCompletionMessageParam

__all__ = ["DeepResearchResource", "AsyncDeepResearchResource"]


class DeepResearchResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DeepResearchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/relax-ai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return DeepResearchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeepResearchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/relax-ai/python-sdk#with_streaming_response
        """
        return DeepResearchResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        messages: Iterable[ChatCompletionMessageParam],
        model: str,
        max_tokens: int | Omit = omit,
        response_format: deep_research_create_params.ResponseFormat | Omit = omit,
        stop: SequenceNotStr[str] | Omit = omit,
        stream: bool | Omit = omit,
        stream_options: StreamOptionsParam | Omit = omit,
        temperature: float | Omit = omit,
        tool_choice: object | Omit = omit,
        tools: Iterable[deep_research_create_params.Tool] | Omit = omit,
        top_p: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeepresearchResponse:
        """
        Performs deep research on a given topic and returns a detailed report.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not is_given(timeout) and self._client.timeout == DEFAULT_TIMEOUT:
            timeout = 600
        return self._post(
            "/v1/deep-research",
            body=maybe_transform(
                {
                    "messages": messages,
                    "model": model,
                    "max_tokens": max_tokens,
                    "response_format": response_format,
                    "stop": stop,
                    "stream": stream,
                    "stream_options": stream_options,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_p": top_p,
                },
                deep_research_create_params.DeepResearchCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeepresearchResponse,
        )


class AsyncDeepResearchResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDeepResearchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/relax-ai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDeepResearchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeepResearchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/relax-ai/python-sdk#with_streaming_response
        """
        return AsyncDeepResearchResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        messages: Iterable[ChatCompletionMessageParam],
        model: str,
        max_tokens: int | Omit = omit,
        response_format: deep_research_create_params.ResponseFormat | Omit = omit,
        stop: SequenceNotStr[str] | Omit = omit,
        stream: bool | Omit = omit,
        stream_options: StreamOptionsParam | Omit = omit,
        temperature: float | Omit = omit,
        tool_choice: object | Omit = omit,
        tools: Iterable[deep_research_create_params.Tool] | Omit = omit,
        top_p: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DeepresearchResponse:
        """
        Performs deep research on a given topic and returns a detailed report.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not is_given(timeout) and self._client.timeout == DEFAULT_TIMEOUT:
            timeout = 600
        return await self._post(
            "/v1/deep-research",
            body=await async_maybe_transform(
                {
                    "messages": messages,
                    "model": model,
                    "max_tokens": max_tokens,
                    "response_format": response_format,
                    "stop": stop,
                    "stream": stream,
                    "stream_options": stream_options,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_p": top_p,
                },
                deep_research_create_params.DeepResearchCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeepresearchResponse,
        )


class DeepResearchResourceWithRawResponse:
    def __init__(self, deep_research: DeepResearchResource) -> None:
        self._deep_research = deep_research

        self.create = to_raw_response_wrapper(
            deep_research.create,
        )


class AsyncDeepResearchResourceWithRawResponse:
    def __init__(self, deep_research: AsyncDeepResearchResource) -> None:
        self._deep_research = deep_research

        self.create = async_to_raw_response_wrapper(
            deep_research.create,
        )


class DeepResearchResourceWithStreamingResponse:
    def __init__(self, deep_research: DeepResearchResource) -> None:
        self._deep_research = deep_research

        self.create = to_streamed_response_wrapper(
            deep_research.create,
        )


class AsyncDeepResearchResourceWithStreamingResponse:
    def __init__(self, deep_research: AsyncDeepResearchResource) -> None:
        self._deep_research = deep_research

        self.create = async_to_streamed_response_wrapper(
            deep_research.create,
        )
