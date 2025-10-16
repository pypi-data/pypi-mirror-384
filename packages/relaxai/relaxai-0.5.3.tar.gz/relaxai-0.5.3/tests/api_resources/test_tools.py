# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from relaxai import Relaxai, AsyncRelaxai
from tests.utils import assert_matches_type
from relaxai.types import ToolResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTools:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_code(self, client: Relaxai) -> None:
        tool = client.tools.execute_code(
            code="code",
            lang="lang",
        )
        assert_matches_type(ToolResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_code_with_all_params(self, client: Relaxai) -> None:
        tool = client.tools.execute_code(
            code="code",
            lang="lang",
            libraries=["string"],
        )
        assert_matches_type(ToolResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_code(self, client: Relaxai) -> None:
        response = client.tools.with_raw_response.execute_code(
            code="code",
            lang="lang",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = response.parse()
        assert_matches_type(ToolResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_code(self, client: Relaxai) -> None:
        with client.tools.with_streaming_response.execute_code(
            code="code",
            lang="lang",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = response.parse()
            assert_matches_type(ToolResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncTools:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_code(self, async_client: AsyncRelaxai) -> None:
        tool = await async_client.tools.execute_code(
            code="code",
            lang="lang",
        )
        assert_matches_type(ToolResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_code_with_all_params(self, async_client: AsyncRelaxai) -> None:
        tool = await async_client.tools.execute_code(
            code="code",
            lang="lang",
            libraries=["string"],
        )
        assert_matches_type(ToolResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_code(self, async_client: AsyncRelaxai) -> None:
        response = await async_client.tools.with_raw_response.execute_code(
            code="code",
            lang="lang",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = await response.parse()
        assert_matches_type(ToolResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_code(self, async_client: AsyncRelaxai) -> None:
        async with async_client.tools.with_streaming_response.execute_code(
            code="code",
            lang="lang",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = await response.parse()
            assert_matches_type(ToolResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True
