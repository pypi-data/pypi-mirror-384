# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from relaxai import Relaxai, AsyncRelaxai
from tests.utils import assert_matches_type
from relaxai.types import DeepresearchResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDeepResearch:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Relaxai) -> None:
        deep_research = client.deep_research.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                }
            ],
            model="model",
        )
        assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Relaxai) -> None:
        deep_research = client.deep_research.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                    "annotations": [
                        {
                            "type": "url_citation",
                            "url_citation": {
                                "end_index": 0,
                                "start_index": 0,
                                "title": "title",
                                "url": "url",
                            },
                        }
                    ],
                    "function_call": {
                        "arguments": "arguments",
                        "name": "name",
                    },
                    "multi_content": [
                        {
                            "image_url": {
                                "detail": "detail",
                                "url": "url",
                            },
                            "text": "text",
                            "type": "type",
                        }
                    ],
                    "name": "name",
                    "reasoning_content": "reasoning_content",
                    "refusal": "refusal",
                    "tool_call_id": "tool_call_id",
                    "tool_calls": [
                        {
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "type",
                            "id": "id",
                            "index": 0,
                        }
                    ],
                }
            ],
            model="model",
            max_tokens=0,
            response_format={
                "json_schema": {
                    "description": "description",
                    "name": "name",
                    "schema": "schema",
                    "strict": True,
                },
                "type": "type",
            },
            stop=["string"],
            stream=True,
            stream_options={"include_usage": True},
            temperature=0,
            tool_choice={},
            tools=[
                {
                    "type": "type",
                    "function": {
                        "name": "name",
                        "parameters": {},
                        "description": "description",
                        "strict": True,
                    },
                }
            ],
            top_p=0,
        )
        assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Relaxai) -> None:
        response = client.deep_research.with_raw_response.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                }
            ],
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        deep_research = response.parse()
        assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Relaxai) -> None:
        with client.deep_research.with_streaming_response.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                }
            ],
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            deep_research = response.parse()
            assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncDeepResearch:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncRelaxai) -> None:
        deep_research = await async_client.deep_research.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                }
            ],
            model="model",
        )
        assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncRelaxai) -> None:
        deep_research = await async_client.deep_research.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                    "annotations": [
                        {
                            "type": "url_citation",
                            "url_citation": {
                                "end_index": 0,
                                "start_index": 0,
                                "title": "title",
                                "url": "url",
                            },
                        }
                    ],
                    "function_call": {
                        "arguments": "arguments",
                        "name": "name",
                    },
                    "multi_content": [
                        {
                            "image_url": {
                                "detail": "detail",
                                "url": "url",
                            },
                            "text": "text",
                            "type": "type",
                        }
                    ],
                    "name": "name",
                    "reasoning_content": "reasoning_content",
                    "refusal": "refusal",
                    "tool_call_id": "tool_call_id",
                    "tool_calls": [
                        {
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "type",
                            "id": "id",
                            "index": 0,
                        }
                    ],
                }
            ],
            model="model",
            max_tokens=0,
            response_format={
                "json_schema": {
                    "description": "description",
                    "name": "name",
                    "schema": "schema",
                    "strict": True,
                },
                "type": "type",
            },
            stop=["string"],
            stream=True,
            stream_options={"include_usage": True},
            temperature=0,
            tool_choice={},
            tools=[
                {
                    "type": "type",
                    "function": {
                        "name": "name",
                        "parameters": {},
                        "description": "description",
                        "strict": True,
                    },
                }
            ],
            top_p=0,
        )
        assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncRelaxai) -> None:
        response = await async_client.deep_research.with_raw_response.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                }
            ],
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        deep_research = await response.parse()
        assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncRelaxai) -> None:
        async with async_client.deep_research.with_streaming_response.create(
            messages=[
                {
                    "content": "content",
                    "role": "role",
                }
            ],
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            deep_research = await response.parse()
            assert_matches_type(DeepresearchResponse, deep_research, path=["response"])

        assert cast(Any, response.is_closed) is True
